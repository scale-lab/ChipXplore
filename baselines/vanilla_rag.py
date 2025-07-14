"""
Vanilla RAG Baseline:
    - Uses one LLMs for the text-to-SQL and text-to-Cypher tasks 
    - No Multi-agents for handling the routing/selection/decomposition... 
    - Uses a top level planner for querying the PDK database and hardware design database. 
"""
import os 
import sys
import re 
import json
import argparse

import langgraph
from langsmith import Client
from langsmith import evaluate
from langgraph.graph import START, END, StateGraph
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

from core.agents.interpreter import Interpreter
from core.agents.refiner import RefinerSQL, RefinerCypher 
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.runner import create_QA
from core.eval.metrics import compute_execution_acc, compute_ves
from core.agents.few_shot.sql import decomposer_few_shot 
from core.eval.test_set import test_queries, test_queries_byview, test_design
from core.agents.few_shot.cypher import cypher_generator_few_shot
from core.utils import get_logger, parse_sql_from_string, parse_cypher_from_string
from core.database.sql import get_desc, get_fk, get_table_names
from core.database.graphdb import  get_node_descr, get_relationship_descr
from core.graph_flow.states import ChipQueryState
from core.graph_flow.reasoner import Reasoner
from core.runner import compute_accuracy, compute_accuracy_cypher

from dotenv import load_dotenv
load_dotenv()

config = None 

VANILLA_RAG_SYS_PROMPT = lambda dialect, desc_str, fk_str, table_info: f"""Given a [Database schema] description, and a [Question], you need to use valid {dialect} and understand the database for text-to-SQL generation.
When generating SQL, we should always consider constraints:

[Constraints]
- In `SELECT <column>`, just select needed columns in the Question without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

[Requirements]
  1. Quote your final SQL with ```sql```

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

[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
"""


VANILLA_RAG_EXAMPLE_ZSHOT = """
[Question]
{input}

Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:
```sql
{query}
```
"""

VANILLA_RAG_SUFFIX_ZSHOT = """
[Question]
{input}

Generate final SQL, considering [Constraints].
"""


class SQLAgent:

    def __init__(self, config: ChipQueryConfig) -> None:
        self.config = config 
        self.desc_str = get_desc(source=None)
        self.fk_str = get_fk(source=None)
        self.table_names = get_table_names(source=None)
        self.table_info = config.db_config.pdk_database.get_table_info(table_names=self.table_names)

        system_prompt = VANILLA_RAG_SYS_PROMPT('SQLite', self.desc_str, self.fk_str, self.table_info)
        system_prompt += """Here are some examples for user questions and their corresponding query decomposition:"""        
        
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            decomposer_few_shot,
            OpenAIEmbeddings(),
            FAISS,
            k=2,
        )

        self.prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(VANILLA_RAG_EXAMPLE_ZSHOT),
            input_variables=["input", "query"],
            prefix=system_prompt,
            suffix=VANILLA_RAG_SUFFIX_ZSHOT
        )

        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm

        self.query_exectutor = RefinerSQL(
            config=config
        )
       
    def forward(self, question):  
        if "deepseek" in self.config.lm_config.generator_lm: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.generator.stream({
                        "input": question, 
                        'desc_str': self.desc_str,
                        'table_info': self.table_info,
                        'fk_str': self.fk_str
                    })
                    
                    full = next(stream)
                    for chunk in stream:
                        full += chunk
                    full
                    received = True 
                except ValueError as e:
                    print(f"[SQL-Agent] Exception Happened Retrying... {e}")
            out = full 
        else: 
            out = self.generator.invoke({
                "input": question, 
                'desc_str': self.desc_str,
                'table_info': self.table_info,
                'fk_str': self.fk_str
            })
    
        if type(out) != str:
            response = out.content 
        else:
            response = out   

        final_sql = parse_sql_from_string(response)

        output = self.query_exectutor.execute(
            {"question": question, 'sql_query': final_sql}
        )
        
        if output['sql_executes']: 
            return {'result': str(output['result']), 'refined_query': output['refined_query'],  'query': [output['refined_query']]}
        else:
            return  {'result': output['error'], 'refined_query': output['refined_query'],  'query': [output['refined_query']]}


CYPHER_VANILLA_SYS_PROMPT = lambda schema, relationship: f"""Given a [Schema] description, and a [Question], you need to use valid Cypher and understand the schema for text-to-Cypher generation.
[Instructions]
- Use only the provided relationship types and properties in the schema.
- Do not use any other relationship types or properties that are not provided.
- Do not include any explanations or apologies in your responses.
- Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
- Do not include any text except the generated Cypher statement.

[Schema]
The database contains a snapshot of the design at different stages: floorplan, placement, cts, and routing. 
{schema}
[Relationships]
{relationship}
""" 

CYPHER_VANILLA_EXAMPLE_PROPMT = """
[Question]
{question}

Generate final Cypher, considering [Instructions]. Give your answer in the same format as the given example:
```cypher
{query}
```
"""

CYPHER_VANILLA_SUFFIX_PROPMT = """[Question]
{question}

Generate final Cypher, considering [Instructions]. Give your answer in the same format as the given example:
"""

class CypherAgent:

    def __init__(self, config) -> None:
        self.config = config 
        node_descr = get_node_descr()
        relationship = get_relationship_descr()
        self.system_prompt = CYPHER_VANILLA_SYS_PROMPT(node_descr, relationship)
        self.system_prompt += """Here are some examples for user questions and their corresponding query:"""        
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            cypher_generator_few_shot,  
            OpenAIEmbeddings(),
            FAISS,
            k=3,           
        )
        self.prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(CYPHER_VANILLA_EXAMPLE_PROPMT), 
            input_variables=["stage", "question", "query"], 
            prefix=self.system_prompt,
            suffix=CYPHER_VANILLA_SUFFIX_PROPMT
        )

        self.query_exectutor = RefinerCypher(
            config=config
        )

        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm 


    def forward(self, question: str):
        if "deepseek" in self.config.lm_config.generator_lm: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.generator.stream({
                        'question': question
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
                'question': question
            })
        cypher_query = parse_cypher_from_string(response.content)
        
        output = self.query_exectutor.execute(
            {"question": question, 'cypher_query': cypher_query}
        )

        if output['cypher_executes']: 
            return {'result': str(output['result']), 'refined_query': output['refined_query'], 'query': [output['refined_query']]}
        else:
            return {'result': output['error'], 'refined_query': output['refined_query'], 'query': [output['refined_query']]}

     


class VanillaRAG:

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
        with open(os.path.join("output", "vanilla_rag.png"), "wb") as f:
            f.write(png_graph)


    def _should_query(self, state: ChipQueryState):
        messages = state.get("messages") 
        last_message = messages[-1].content
        print("Last Message: ", last_message)
        json_object = self._extract_json(last_message)
        print("JSON Object: ", json_object)
        
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
            output = self.graph.invoke({"question": question}, {"recursion_limit": self.config.flow_config.graph_recursion_limit})
            response = {
                'messages': output['messages'], 
                'final_answer': output['messages'][-1].content, 
                'query': output['query']
            }
        except langgraph.errors.GraphRecursionError:
            print("[Error] Hit graph recursion limit!!!")
            response = {
                'messages': [], 
                'final_answer': "", 
                'query': ""
            } 

        return response 
    

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
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/baselines/vanilla_rag.log')
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
        'lef': "PDK-LEF-QA-Vanilla-RAG",
        "tlef": "PDK-TechLEF-QA-Vanilla-RAG",
        "lib": "PDK-LIB-QA-Vanilla-RAG"
    }
    design_dataset_name = "Design-QA-Vanilla-RAG"

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
        flow_config=FlowConfigs(
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
            partition=False
        )
    )

    vanilla_rag = VanillaRAG(
        config=config, 
    )
    
    def answer(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = vanilla_rag.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['final_answer']}")
        return output
    
    def answer_pdk(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = vanilla_rag.pdk_agent.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['query']}")
        return output

    def answer_design(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = vanilla_rag.design_agent.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['query']}")
        return output
    
    for key in ["lef", "tlef", "lib"]: 
        pdk_qa_results = evaluate(
            answer_pdk, 
            data=pdk_dataset_name[key],
            experiment_prefix=f"Vanilla-RAG+{model}",
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
    #     experiment_prefix=f"Vanilla-RAG+{model}",
    #     evaluators=[compute_accuracy_cypher],
    #     max_concurrency=1
    # )
    # design_qa_results.wait()

    # ex = design_qa_results._results[0]['evaluation_results']['results'][0].score
    # ves = design_qa_results._results[0]['evaluation_results']['results'][1].score
    
    # logger.info(f"YELLOW: Execution Accuracy (DEF), {ex}, Valid Efficiency Score (DEF), {ves}")

 
    # try: 
    #     output = vanilla_rag.forward("How many cells are in the high density library ?")
    # except langgraph.errors.GraphRecursionError:
    #     print("Hit Recursion Limit!!")
    # for m in output['messages']:
    #     m.pretty_print()

    # output = vanilla_rag.forward("How many cells are in the design ?")

    # for m in output['messages']:
    #     m.pretty_print()



if __name__ == '__main__':
    main()