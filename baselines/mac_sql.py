"""
MAC-SQL Baseline:
    - Uses on the MAC-SQL archietecture for the text-to-SQL and text-to-Cypher tasks 
    - No agent for performing routing and no database paritioning 
    - Still uses a top level planner for querying the PDK database and hardware design database. 
    - Uses sequential chaining instead of agents instead of parallelizing agent calls.
"""
import os 
import re
import json
import argparse


import langgraph
from langsmith import Client
from langsmith import evaluate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langgraph.graph import START, END, StateGraph


from core.runner import create_QA
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.utils import get_logger, parse_sql_from_string, parse_cypher_from_string
from core.agents.few_shot.sql import decomposer_few_shot 
from core.agents.few_shot.cypher import cypher_generator_few_shot
from core.agents.selectors.table_selector import SchemaSelector
from core.agents.selectors.node_selector import NodeSelector
from core.agents.refiner import RefinerSQL, RefinerCypher
from core.agents.interpreter import Interpreter
from core.eval.test_set import  test_queries_byview, test_design
from core.graph_flow.reasoner import Reasoner
from core.graph_flow.states import ChipQueryState
from core.runner import compute_accuracy, compute_accuracy_cypher
from core.eval.metrics import compute_execution_acc, compute_ves

from dotenv import load_dotenv
load_dotenv()

config = None 


DIN_MAC_SQL_SYS_PROMPT = lambda dialect: f"""Given a [Database schema] description, and a [Question], you need to use valid {dialect} and understand the database, and then decompose the question into subquestions for text-to-SQL generation.
When generating SQL, we should always consider constraints:

[Constraints]
- In `SELECT <column>`, just select needed columns in the Question without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- Your final SQL query must be a one statement. Database can't execute multiple statements. 

[Requirements]
  1. You must reason about operating conditions and the standard cell variant relevant to the question to filter entries related to the operating condition and the standard cell variant the question is referring to. 
  2. Generate a SQL for each sub-query, then generate a final SQL for the input question [Question].
  3. You must output your answer in the same format as the given examples. 

[Hints]
- All cell names in the library are prefixed with a variant-specific prefix. For example,: 
  - HighDensity Prefix is sky130_fd_sc_hd
  - HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
  - HighSpeed Prefix is sky130_fd_sc_hs
  - LowSpeed Prefix is sky130_fd_sc_ls
  - MediumSpeed Prefix is sky130_fd_sc_ms
  - LowPower Prefix is sky130_fd_sc_lp
- For example, the and2_1 cell in the : 
  - high density library is named 'sky130_fd_sc_hd__and2_1'
  - high density low leakage library is named 'sky130_fd_sc_hdll__and2_1'
  - high speed library is named 'sky130_fd_sc_hs__and2_1' 
  - low speed library is named 'sky130_fd_sc_ls__and2_1'
  - medium sped library is named 'sky130_fd_sc_ms__and2_1' 
  - low power library is named 'sky130_fd_sc_lp__and2_1'
"""


DIN_MAC_SQL_EXAMPLE_SUBQ = """
[Database schema]
{desc_str}
[Foreign keys]
{fk_str}
[Question]
{input}

Decompose the question into sub questions, considering [Constraints], and generate the final SQL after thinking step by step:
{decompose_str}
"""


DIN_MAC_SQL_SUFFIX_SUBQ = """
[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
[Question]
{input}

Decompose the question into sub questions, considering [Constraints], and generate the final SQL after thinking step by step. Give your answer in the same format as the given example:
"""


class SQLAgent:

    def __init__(self, config) -> None:
        self.config = config 
        system_prompt = DIN_MAC_SQL_SYS_PROMPT('SQLite')
        EXAMPLE_PROPMT = DIN_MAC_SQL_EXAMPLE_SUBQ
        SUFFIX_PROMPT = DIN_MAC_SQL_SUFFIX_SUBQ 
        
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            decomposer_few_shot,
            OpenAIEmbeddings(),
            FAISS,
            k=2,
        )

        self.prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(EXAMPLE_PROPMT),
            input_variables=["input", "desc_str", "fk_str", "decompose_str"],
            prefix=system_prompt,
            suffix=SUFFIX_PROMPT
        )
        
        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
        
        self.selector = SchemaSelector(
            config=config,
            custom_selector=False
        )

        self.refiner = RefinerSQL(
            config=config,
        )
        

    def forward(self, question):

        output = self.selector.select(
            {"view": "", "question": question} 
        ) 
        
        fk_str = output['fk_str']
        descr_str = output['desc_str']
        table_info = output['table_info']

        if "deepseek-chat" in self.config.lm_config.generator_lm: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.generator.stream({
                        "input": question,
                        "desc_str": descr_str,
                        "table_info": table_info,
                        'fk_str': fk_str,
                    })
                    full = next(stream)
                    for chunk in stream:
                        full += chunk
                    full
                    received = True 
                except ValueError as e:
                    print(f"[SQL-Agent] Exception Happened Retrying... {e}")
            response = full 
        else: 
            response = self.generator.invoke({
                "input": question,
                "desc_str": descr_str,
                "table_info": table_info,
                'fk_str': fk_str,
            })


        final_sql = parse_sql_from_string(response.content)

        executer_response = self.refiner.execute(
            {"question": question, 'sql_query': final_sql}
        )

        refine_iters = 0
        refined_sql = final_sql
        while not executer_response['sql_executes'] and refine_iters < self.config.flow_config.max_refine_iters: 
            refiner_response = self.refiner.refine({
                "question": question, 
                "fk_str": fk_str, 
                "descr_str": descr_str,
                "error": executer_response["error"],
                "table_info": table_info,
                "scl_library": "",
                "sql_query": final_sql, 
                "refined_query": refined_sql,
                "exception_class": executer_response["exception_class"],
                "op_cond": ""
            })
            refine_iters += 1 
            refined_sql = refiner_response["refined_query"]

            executer_response = self.refiner.execute(
                {"question": question, 'sql_query': refined_sql}
            )
            
        if executer_response['sql_executes']: 
            return {'result': str(executer_response['result']), 'refined_query': executer_response['refined_query'], 'query': [executer_response['refined_query']]}
        else:
            return {'result': str(executer_response['error']), 'refined_query': executer_response['refined_query'], 'query': [executer_response['refined_query']]}

        


CYPHER_MAC_SYS_PROMPT = """
Given a [Schema] description, and a [Question], you need to use valid Cypher and understand the schema, and then decompose the question into subquestions for text-to-Cypher generation.
[Instructions]
- Use only the provided relationship types and properties in the schema.
- Do not use any other relationship types or properties that are not provided.
- Do not include any explanations or apologies in your responses.
- Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
- Do not include any text except the generated Cypher statement.

The database contains the design information at different physical design stages:

- floorplan
- placement
- cts 
- routing 

Reason first about the relevant stage to answer the user question and use the stage in your final cypher query.
""" 

CYPHER_MAC_EXAMPLE_PROMPT =  """
[Schema]
{schema}
[Relationships]
{relationship}
[Question]
{question}

Decompose the question into sub questions and generate the Cypher after thinking step by step. 
{decompose_str}
"""

CYPHER_MAC_SUFFIX = """
[Schema]
{schema}
[Relationships]
{relationship}
[Question]
{question}

Decompose the question into sub questions and generate the Cypher after thinking step by step. Give your answer in the same format as the given example:
"""

class CypherAgent:

    def __init__(self, config) -> None:
        
        self.config = config         
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            cypher_generator_few_shot,  
            OpenAIEmbeddings(),
            FAISS,
            k=3,           
        )

        self.prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(CYPHER_MAC_EXAMPLE_PROMPT), 
            input_variables=["question", "query", "schema", "relationship", "decompose_str"], 
            prefix=CYPHER_MAC_SYS_PROMPT,
            suffix=CYPHER_MAC_SUFFIX
        )
        
        self.selector = NodeSelector(
            config=config,
        )

        self.refiner = RefinerCypher(
            config=config
        )

        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
        

    def forward(self, question):
        output = self.selector.select(
            {"question": question} 
        ) 
        
        node_descr = output['node_descr']
        edges = output['edges']

        if "deepseek-chat" in self.config.lm_config.generator_lm: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.generator.stream({
                        "question": question,
                        "schema": node_descr,
                        "relationship": edges
                    })
                    full = next(stream)
                    for chunk in stream:
                        full += chunk
                    full
                    received = True 
                except ValueError as e:
                    print(f"[SQL-Agent] Exception Happened Retrying... {e}")
            response = full 
        else: 
            response = self.generator.invoke({
                "question": question,
                "schema": node_descr,
                "relationship": edges
            })


        final_cypher = parse_cypher_from_string(response.content)

        executer_response = self.refiner.execute(
            { 'cypher_query': final_cypher}
        )


        refine_iters = 0
        refined_query = final_cypher        
        while not executer_response['cypher_executes'] and refine_iters < self.config.flow_config.max_refine_iters: 
            refiner_response = self.refiner.refine({
                "question": question, 
                "stage": "",
                "error": executer_response["error"],
                "node_descr": node_descr,
                "edges": edges,
                "cypher_query": final_cypher, 
                "refined_query": refined_query,
                "exception_class": executer_response["exception_class"],
                "op_cond": ""
            })
            refine_iters += 1 
            refined_query = refiner_response["refined_query"]

            executer_response = self.refiner.execute(
                {"question": question, 'sql_query': refined_query}
            )
            
        if executer_response['cypher_executes']: 
            return {'result': str(executer_response['result']), 'refined_query': executer_response['refined_query'], 'query': [executer_response['refined_query']]}
        else:
            return {'result': str(executer_response['error']), 'refined_query': executer_response['refined_query'], 'query': [executer_response['refined_query']]}

      
class MACSQL:

    def __init__(self, config) -> None:
        self.config = config 
        self.pdk_agent = SQLAgent(
            config=config
        )
        self.design_agent = CypherAgent(
            config=config
        )
        
        self.interpreter = Interpreter(
            config=config
        )

        def pdk_query(
            state: ChipQueryState,
        ):
            messages = state.get("messages")
            last_message = messages[-1].content 
            json_object = self._extract_json(last_message)
            question = json_object["args"]
            if type(question) == dict:
                question = question["question"]
            
            output = self.pdk_agent.forward(question)
           
            return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"pdk_query tool output: {output['result']}"}
        

        def design_query(
            state: ChipQueryState, 
        ):
            messages = state.get("messages")
            last_message = messages[-1].content 
            json_object = self._extract_json(last_message)
            question = json_object["args"]
            if type(question) == dict:
                question = question["question"]
            
            output = self.design_agent.forward(question)
           
            return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"design_query tool output: {output['result']}"}
        
    
        def finish(
            state: ChipQueryState, 
        ):
            output = self.interpreter.interpret(
                state=state
            )
            print("Final answer is: ", output)
            return {"final_answer": output}
        
        reasoner = Reasoner(
            config=config,
        )

        self.builder = StateGraph(ChipQueryState)
        self.builder.add_node("reasoner", reasoner.forward)
        self.builder.add_node("design_query", design_query)
        self.builder.add_node("pdk_query", pdk_query)
        self.builder.add_node("finish", finish)
        self.builder.add_edge(START, "reasoner")
        self.builder.add_conditional_edges(
            "reasoner",
            self._should_query
        )
        self.builder.add_edge("design_query", "reasoner")
        self.builder.add_edge("pdk_query", "reasoner")
        self.builder.add_edge("finish", END)
        self.graph = self.builder.compile()

        png_graph = self.graph.get_graph().draw_mermaid_png()
        with open(os.path.join("output", "mac_sql.png"), "wb") as f:
            f.write(png_graph)

    
    def _should_query(self, state: ChipQueryState):
        messages = state.get("messages") 
        last_message = messages[-1].content
        json_object = self._extract_json(last_message)
        
        if json_object["action"] == "design_query": 
            return "design_query"
        
        if json_object["action"] == "pdk_query":
            return "pdk_query"
        
        if json_object["action"] == "finish":
            return "finish"
    
    def _extract_json(self, text):
        text = re.sub(r'```json\s*|\s*```', '', text).strip()
        json_match = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', text, re.DOTALL)
        if json_match:
            json_content = json_match.group(0)
            try:
                return json.loads(json_content)  # Parse JSON
            except json.JSONDecodeError:
                raise ValueError("Extracted JSON is invalid.")
        else:
            raise ValueError("No valid JSON found in the input.")

    def forward(self, question):
        try: 
            output = self.graph.invoke({"question": question}, {"recursion_limit": config.flow_config.graph_recursion_limit})
            return {
                'messages': output['messages'], 
                'final_answer': output['messages'][-1].content, 
                'query': output['query']
            }

        except langgraph.errors.GraphRecursionError:
            return {
                'messages': [],
                'final_answer': "",
                'query': []
            }
        except json.JSONDecodeError: 
            self.forward(question=question) # call the function again until it works
        
     

def compute_accuracy(run, example) -> dict:
    global config 
    predicted_query = run.outputs.get("query")
    ground_truth_query = example.outputs.get("query")
    
    execution_accuracy = compute_execution_acc(
        predicted_queries=predicted_query, 
        ground_truth_queries=[ground_truth_query],
        database=config.db_config.pdk_database
    )

    valid_efficiency_score = compute_ves(
        predicted_queries=predicted_query,
        ground_truth=[ground_truth_query],
        database=config.db_config.pdk_database,
        num_iters=3
    )

    return {
        "results": [
            {"key": "execution_accuracy", "score": execution_accuracy},
            {"key": "valid_efficiency_score", "score": valid_efficiency_score}
        ]
    }


def compute_accuracy_cypher(run, example) -> dict:
    global config 
    predicted_query = run.outputs.get("query")
    ground_truth_query = example.outputs.get("query")
    
    execution_accuracy = compute_execution_acc(
        predicted_queries=predicted_query, 
        ground_truth_queries=[ground_truth_query],
        database=config.db_config.design_database,
        use_cypher=True
    )

    valid_efficiency_score = compute_ves(
        predicted_queries=predicted_query,
        ground_truth=[ground_truth_query],
        database=config.db_config.design_database,
        num_iters=3,
        use_cypher=True
    )

    return {
        "results": [
            {"key": "execution_accuracy", "score": execution_accuracy},
            {"key": "valid_efficiency_score", "score": valid_efficiency_score}
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/design_graph_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--temperature', type=int, help='Model name', default=0)
    parser.add_argument('--filter', type=str, help='Filter examples to run by view, (lib, lef, tlef)', default='')
    args = parser.parse_args()
   
    output = args.output
    model = args.model 
    filter = args.filter 

    logger = get_logger(output)

    client = Client()

    pdk_dataset_name = {
        'lef': "PDK-LEF-QA-MAC-SQL",
        "tlef": "PDK-TechLEF-QA-MAC-SQL",
        "lib": "PDK-LIB-QA-MAC-SQL"
    }
    design_dataset_name = "Design-QA-MAC-SQL"

    create_QA(
        client=client, 
        pdk_dataset_name=pdk_dataset_name,
        design_dataset_name=design_dataset_name,
        test_set_pdk=test_queries_byview, 
        test_set_design=test_design, 
        filter=filter
    )

    global config

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            graph_recursion_limit=6
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=model
        ),
        db_config=DatabaseConfig(
            in_mem_db=True,
            partition=False
        )
    )  

    mac_sql = MACSQL(
        config=config
    )

    # def answer(input):
    #     logger.info(f"BLUE: User question is {input['question']}")
    #     output = mac_sql.forward(
    #         question=input['question']
    #     )
    #     logger.info(f"YELLOW: ***LLM Output is***: \n {output['final_answer']}")
    #     return output

    def answer_pdk(input):
        logger.info(f"BLUE: User question is {input['question']}")
        try: 
            output = mac_sql.pdk_agent.forward(
                question=input['question']
            )
        except json.JSONDecodeError:
            output = answer_pdk(input=input)

        logger.info(f"YELLOW: ***LLM Output is***: \n {output['refined_query']}")
        return output
    
    def answer_design(input):
        logger.info(f"BLUE: User question is {input['question']}")
        try: 
            output = mac_sql.design_agent.forward(
                question=input['question']
            )
        except json.JSONDecodeError:
            output = answer_design(input=input)

        logger.info(f"YELLOW: ***LLM Output is***: \n {output['query']}")
        return output
    
    for key in ["lib"]: 
        pdk_qa_results = evaluate(
            answer_pdk, 
            data=pdk_dataset_name[key],
            experiment_prefix=f"mac-sql+{model}",
            evaluators=[compute_accuracy],
            max_concurrency=1
        )

        pdk_qa_results.wait()

        ex = pdk_qa_results._results[0]['evaluation_results']['results'][0].score
        ves = pdk_qa_results._results[0]['evaluation_results']['results'][1].score
        
        logger.info(f"YELLOW: Execution Accuracy (PDK-{key}), {ex}, Valid Efficiency Score (PDK-{key}), {ves}")


    # design_qa_results = evaluate(
    #     answer_design, 
    #     data=design_dataset_name,
    #     experiment_prefix=f"mac-sql-{model}",
    #     evaluators=[compute_accuracy_cypher],
    #     max_concurrency=1
    # )

    # ex = design_qa_results._results[0]['evaluation_results']['results'][0].score
    # ves = design_qa_results._results[0]['evaluation_results']['results'][1].score
    
    # logger.info(f"YELLOW: Execution Accuracy (DEF), {ex}, Valid Efficiency Score (DEF), {ves}")

    # try: 
    #     output = mac_sql.forward(
    #        question="How many cells are in the high density library ?"
    #     )
    # except langgraph.errors.GraphRecursionError:
    #     print("Hit Recursion Limit!!")


    # # print(output)
    
    # try: 
    #     output = mac_sql.forward("How many cells are in the design ?")
    #     print(output)
    # except langgraph.errors.GraphRecursionError:
    #     print("Hit Recursion Limit!!")
    
    # for m in output['messages']:
    #     m.pretty_print()



if __name__ == '__main__':
    main()