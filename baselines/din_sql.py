"""
DIN-SQL Baseline:
    - Uses on the DIN-SQL archietecture for the text-to-SQL and text-to-Cypher tasks 
    - No agent for performing routing and no database paritioning 
    - Still uses a top level planner for querying the PDK database and hardware design database. 
"""
import re 
import os 
import time 
import argparse

from typing_extensions import Any, Annotated

import langgraph
from langsmith import Client
from langsmith import evaluate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain.prompts import PromptTemplate
from langchain.chains.prompt_selector import ConditionalPromptSelector

from core.runner import create_QA
from config.sky130 import View
from core.agents.refiner import RefinerSQL, RefinerCypher 
from core.agents.interpreter import Interpreter
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.utils import get_logger, parse_sql_from_string, parse_cypher_from_string
from core.agents.utils import parse_json_from_string
from core.agents.few_shot.sql import decomposer_few_shot 
from core.agents.few_shot.cypher import cypher_generator_few_shot
from core.agents.selectors.table_selector import SchemaSelector
from core.agents.selectors.node_selector import NodeSelector
from core.agents.refiner import RefinerSQL
from core.eval.test_set import  test_queries_byview, test_design
from core.graph_flow.reasoner import Reasoner
from core.graph_flow.states import ChipQueryState
from core.runner import compute_accuracy, compute_accuracy_cypher
from core.eval.metrics import compute_execution_acc, compute_ves
from core.database.sql import get_desc, get_fk, get_table_names
from core.database.graphdb import get_node_descr, get_relationship_descr_verbose, get_relationship_descr
from core.eval.interwined_questions import test_queries_interwined
from baselines.din_sql_prompts import SCHEMA_LINKER_SYS_PROMPT, CYPHER_SCHEMA_LINKERS, QUERY_CLASSIFIER_SYS_PROMPT, CYPHER_NESTED_COMPLEX_SYS_PROMPT, CYPHER_QUERY_CLASSIFIER_SYS_PROMPT, EASY_SYS_PROMPT, CYPHER_EASY_SYS_PROMPT, NESTED_COMPLEX_SYS_PROPMT, CYPHER_NON_NESTED_SYS_PROMPT, NON_NESTED_SYS_PROPMT


from dotenv import load_dotenv
load_dotenv()

config = None 


class SchemaLinkerSQL: 

    def __init__(self, config):
        
        USER_TEMPLATE = """
Q: {question}
Schema_links:
"""
        lib_table_descr = get_desc(source=View.Liberty.value)
        lef_table_descr = get_desc(source=View.Lef.value)
        tlef_table_descr = get_desc(source=View.TechLef.value)

        lib_fk_str = get_fk(source=View.Liberty.value)
        lef_fk_str = get_fk(source=View.Lef.value)
        tlef_fk_str = get_fk(source=View.TechLef.value)

        lib_table_names = get_table_names(
            source=View.Liberty.value, 
            partition=config.db_config.partition
        )
        lef_table_names = get_table_names(
            source=View.Lef.value, 
            partition=config.db_config.partition
        )
        tlef_table_names = get_table_names(
            source=View.TechLef.value, 
            partition=config.db_config.partition
        )

        lib_table_info =  config.db_config.pdk_database.get_table_info(table_names=lib_table_names)
        lef_table_info =  config.db_config.pdk_database.get_table_info(table_names=lef_table_names)
        tlef_table_info =  config.db_config.pdk_database.get_table_info(table_names=tlef_table_names)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(SCHEMA_LINKER_SYS_PROMPT(
                    lef_table_descr=lef_table_descr,
                    lef_table_info=lef_table_info,
                    lef_fk_str=lef_fk_str,
                    lib_table_descr=lib_table_descr,
                    lib_table_info=lib_table_info,
                    lib_fk_str=lib_fk_str,                    
                    tlef_table_descr=tlef_table_descr,
                    tlef_table_info=tlef_table_info,
                    tlef_fk_str=tlef_fk_str,
                ))),
                ("user", USER_TEMPLATE),
            ]
        )
            
        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
        
        
    def _parse_schema_links(self, text):
        match = re.search(r'Schema_links:\s*(\[[^\]]+\])', text)
        if match:
            return match.group(1).strip()
        return None
    
    def link(self, question):
        out = self.generator.invoke({"question": question})
        schema_links = self._parse_schema_links(out.content)
        return schema_links


class SchemaLinkerCypher: 

    def __init__(self, config):
        
        USER_TEMPLATE = """
Q: {question}
Schema_links:
"""
        node_descr = get_node_descr()
        edges = get_relationship_descr_verbose()

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(CYPHER_SCHEMA_LINKERS(
                    node_descr=node_descr,
                    relationship_descr=edges
                ))),
                ("user", USER_TEMPLATE),
            ]
        )
            
        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
        
        
    def _parse_schema_links(self, text):
        match = re.search(r'Schema_links:\s*(\[[^\]]+\])', text)
        if match:
            return match.group(1).strip()
        return None
    
    def link(self, question):
        out = self.generator.invoke({"question": question})
        schema_links = self._parse_schema_links(out.content)
        return schema_links


class QueryClassifierSQL:

    def __init__(self, config) -> None:
        # classifies each query into one of the three classes: easy, non-nested complex and nested complex
        USER_TEMPLATE = """
        Q: {question}
        schema_links: {schema_link}
        """

        table_descr = get_desc(source="")
        fk_str = get_fk(source="")
        lib_table_descr = get_desc(source=View.Liberty.value)
        lef_table_descr = get_desc(source=View.Lef.value)
        tlef_table_descr = get_desc(source=View.TechLef.value)

        lib_fk_str = get_fk(source=View.Liberty.value)
        lef_fk_str = get_fk(source=View.Lef.value)
        tlef_fk_str = get_fk(source=View.TechLef.value)

        lib_table_names = get_table_names(
            source=View.Liberty.value, 
            partition=config.db_config.partition
        )
        lef_table_names = get_table_names(
            source=View.Lef.value, 
            partition=config.db_config.partition
        )
        tlef_table_names = get_table_names(
            source=View.TechLef.value, 
            partition=config.db_config.partition
        )

        lib_table_info =  config.db_config.pdk_database.get_table_info(table_names=lib_table_names)
        lef_table_info =  config.db_config.pdk_database.get_table_info(table_names=lef_table_names)
        tlef_table_info =  config.db_config.pdk_database.get_table_info(table_names=tlef_table_names)


        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(QUERY_CLASSIFIER_SYS_PROMPT(
                    lef_table_descr=lef_table_descr,
                    lef_table_info=lef_table_info,
                    lef_fk_str=lef_fk_str,
                    lib_table_descr=lib_table_descr,
                    lib_table_info=lib_table_info,
                    lib_fk_str=lib_fk_str,                    
                    tlef_table_descr=tlef_table_descr,
                    tlef_table_info=tlef_table_info,
                    tlef_fk_str=tlef_fk_str,
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
    
    def _parse_label(self, text):
        json_content = parse_json_from_string(text)
        return json_content["label"]

    def forward(self, question, schema_link):
        out = self.generator.invoke({"question": question, "schema_link": schema_link})
        label = self._parse_label(out.content)
        return label





class QueryClassifierCypher:

    def __init__(self, config) -> None:
        USER_TEMPLATE = """
        Q: {question}
        schema_links: {schema_link}
        """


        node_descr = get_node_descr()
        edges = get_relationship_descr_verbose()

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(CYPHER_QUERY_CLASSIFIER_SYS_PROMPT(
                   node_descr=node_descr,
                   relationship_descr=edges
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        self.llm = config.lm_config.generator_llm_model
        self.generator = self.prompt | self.llm
    
    def _parse_label(self, text):
        json_content = parse_json_from_string(text)
        return json_content["label"]

    def forward(self, question, schema_link):
        out = self.generator.invoke({"question": question, "schema_link": schema_link})
        label = self._parse_label(out.content)
        return label



class QueryGeneratorSQL:

    def __init__(self, config):
        self.config = config 
        lib_table_descr = get_desc(source=View.Liberty.value)
        lef_table_descr = get_desc(source=View.Lef.value)
        tlef_table_descr = get_desc(source=View.TechLef.value)

        lib_fk_str = get_fk(source=View.Liberty.value)
        lef_fk_str = get_fk(source=View.Lef.value)
        tlef_fk_str = get_fk(source=View.TechLef.value)

        lib_table_names = get_table_names(
            source=View.Liberty.value, 
            partition=config.db_config.partition
        )
        lef_table_names = get_table_names(
            source=View.Lef.value, 
            partition=config.db_config.partition
        )
        tlef_table_names = get_table_names(
            source=View.TechLef.value, 
            partition=config.db_config.partition
        )

        lib_table_info =  config.db_config.pdk_database.get_table_info(table_names=lib_table_names)
        lef_table_info =  config.db_config.pdk_database.get_table_info(table_names=lef_table_names)
        tlef_table_info =  config.db_config.pdk_database.get_table_info(table_names=tlef_table_names)


        USER_TEMPLATE = """
Output SQL for the given user question. Give your reasoning first, then output the SQL. 

Q: {question}
Schema_links: {schema_link}
"""

        easy_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(EASY_SYS_PROMPT(
                    lef_table_descr=lef_table_descr,
                    lef_table_info=lef_table_info,
                    lef_fk_str=lef_fk_str,
                    lib_table_descr=lib_table_descr,
                    lib_table_info=lib_table_info,
                    lib_fk_str=lib_fk_str,                    
                    tlef_table_descr=tlef_table_descr,
                    tlef_table_info=tlef_table_info,
                    tlef_fk_str=tlef_fk_str,
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        non_nested_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(NON_NESTED_SYS_PROPMT(
                    lef_table_descr=lef_table_descr,
                    lef_table_info=lef_table_info,
                    lef_fk_str=lef_fk_str,
                    lib_table_descr=lib_table_descr,
                    lib_table_info=lib_table_info,
                    lib_fk_str=lib_fk_str,                    
                    tlef_table_descr=tlef_table_descr,
                    tlef_table_info=tlef_table_info,
                    tlef_fk_str=tlef_fk_str,

                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        nested_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(NESTED_COMPLEX_SYS_PROPMT(
                    lef_table_descr=lef_table_descr,
                    lef_table_info=lef_table_info,
                    lef_fk_str=lef_fk_str,
                    lib_table_descr=lib_table_descr,
                    lib_table_info=lib_table_info,
                    lib_fk_str=lib_fk_str,                    
                    tlef_table_descr=tlef_table_descr,
                    tlef_table_info=tlef_table_info,
                    tlef_fk_str=tlef_fk_str,

                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        self.prompt_selector = ConditionalPromptSelector(
            default_prompt=easy_prompt,
            conditionals=[
                (lambda label: "NESTED" in label, nested_prompt), 
                (lambda label: "NON-NESTED" in label, non_nested_prompt), 
            ]
        )

        self.llm = config.lm_config.generator_llm_model


    def _extract_sql(self, query_text: str) -> str:
        pattern = r"```sql\s*(.*?)\s*```"
        sql_blocks = re.findall(pattern, query_text, re.DOTALL)
        if sql_blocks:
            return sql_blocks[-1]
        else:
            return None 

    def forward(self, question, schema_links, label):
        selected_prompt = self.prompt_selector.get_prompt(label)
        generator = selected_prompt | self.llm 
        output = generator.invoke({"question": question, "schema_link": schema_links})
        query = self._extract_sql(output.content)
        return query 



class QueryGeneratorCypher:

    def __init__(self, config):
        self.config = config 
        
        node_descr = get_node_descr()
        edges = get_relationship_descr_verbose()

     
        USER_TEMPLATE = """
Output SQL for the given user question. Give your reasoning first, then output the SQL. 

Q: {question}
Schema_links: {schema_link}
"""

        easy_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(CYPHER_EASY_SYS_PROMPT(
                    node_descr=node_descr,
                    relationship_descr=edges
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        non_nested_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(CYPHER_NON_NESTED_SYS_PROMPT(
                    node_descr=node_descr,
                    relationship_descr=edges
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        nested_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(CYPHER_NESTED_COMPLEX_SYS_PROMPT(
                    node_descr=node_descr,
                    relationship_descr=edges
                ))),
                ("user", USER_TEMPLATE),
            ]
        )

        self.prompt_selector = ConditionalPromptSelector(
            default_prompt=easy_prompt,
            conditionals=[
                (lambda label: "NESTED" in label, nested_prompt), 
                (lambda label: "NON-NESTED" in label, non_nested_prompt), 
            ]
        )

        self.llm = config.lm_config.generator_llm_model


    def _extract_sql(self, query_text: str) -> str:
        pattern = r"```sql\s*(.*?)\s*```"
        sql_blocks = re.findall(pattern, query_text, re.DOTALL)
        if sql_blocks:
            return sql_blocks[-1]
        else:
            return None 

    def forward(self, question, schema_links, label):
        selected_prompt = self.prompt_selector.get_prompt(label)
        generator = selected_prompt | self.llm 
        output = generator.invoke({"question": question, "schema_link": schema_links})
        query = self._extract_sql(output.content)
        return query 


class SQLAgent:

    def __init__(self, config) -> None:
        self.config = config 
        self.schema_linker = SchemaLinkerSQL(
            config=config
        )

        self.classifier = QueryClassifierSQL(
            config=config
        )

        self.query_generator = QueryGeneratorSQL(
            config=config
        ) 
        
        self.refiner = RefinerSQL(
            config=config,
        )

        self.table_descr = get_desc(source=None)
        self.fk_str = get_fk(source=None) 
        table_names = get_table_names(source=None)
        self.table_info = config.db_config.pdk_database.get_table_info(table_names=table_names)

    def forward(self, question):
        schema_link = self.schema_linker.link(
           question=question
        ) 

        label = self.classifier.forward(
            schema_link=schema_link,
            question=question
        )

        query = self.query_generator.forward(
            question=question,
            schema_links=schema_link,
            label=label
        )

        executer_response = self.refiner.execute(
            {"question": question, 'sql_query': query}
        )

        refine_iters = 0
        refined_sql = query
        print("Query is: ", refined_sql)
        print(executer_response['sql_executes'])
        while not executer_response['sql_executes'] and refine_iters < self.config.flow_config.max_refine_iters: 
            refiner_response = self.refiner.refine({
                "question": question, 
                "fk_str": self.fk_str, 
                "descr_str": self.table_descr,
                "error": executer_response["error"],
                "table_info": self.table_info,
                "scl_library": "",
                "sql_query": query, 
                "refined_query": refined_sql,
                "exception_class": executer_response["exception_class"],
                "op_cond": ""
            })
            refine_iters += 1 
            refined_sql = refiner_response["refined_query"]

            executer_response = self.refiner.execute(
                {"question": question, 'sql_query': refined_sql}
            )

            print("REFINERING Queyr: ", refined_sql)

        print("Query is: ", refined_sql)

        return {"query": [refined_sql], "result": executer_response['result'] } 
    

class CypherAgent:

    def __init__(self, config) -> None:
        self.config = config 
        self.schema_linker = SchemaLinkerCypher(
            config=config
        )

        self.classifier = QueryClassifierCypher(
            config=config
        )

        self.query_generator = QueryGeneratorCypher(
            config=config
        ) 
        
        self.refiner = RefinerCypher(
            config=config,
        )

                
        self.node_descr = get_node_descr()
        self.edges = get_relationship_descr_verbose()


    def forward(self, question):
        schema_link = self.schema_linker.link(
           question=question
        ) 

        label = self.classifier.forward(
            schema_link=schema_link,
            question=question
        )

        query = self.query_generator.forward(
            question=question,
            schema_links=schema_link,
            label=label
        )

        executer_response = self.refiner.execute(
            {"question": question, 'sql_query': query}
        )

        refine_iters = 0
        refined_query = query        
        while not executer_response['cypher_executes'] and refine_iters < self.config.flow_config.max_refine_iters: 
            refiner_response = self.refiner.refine({
                "question": question, 
                "stage": "",
                "error": executer_response["error"],
                "node_descr": self.node_descr,
                "edges": self.edges,
                "cypher_query": query, 
                "refined_query": refined_query,
                "exception_class": executer_response["exception_class"],
                "op_cond": ""
            })
            refine_iters += 1 
            refined_query = refiner_response["refined_query"]

            executer_response = self.refiner.execute(
                {"question": question, 'sql_query': refined_query}
            )
 

        return {"query": [refined_query], "result": executer_response['result'] } 
    




class DINSQL():


    def __init__(self, config):
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

    def forward(self, question):
        output = self.pdk_agent.forward(question) 
        return output


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
        'lef': "PDK-LEF-QA-DIN-SQL",
        "tlef": "PDK-TechLEF-QA-DIN-SQL",
        "lib": "PDK-LIB-QA-DIN-SQL"
    }
    design_dataset_name = "Design-QA-DIN-SQL"
    interwined_dataset_name = "Interwined-QA-Chip-Query"


    create_QA(
        client=client, 
        pdk_dataset_name=pdk_dataset_name,
        design_dataset_name=design_dataset_name,
        interwined_dataset_name=interwined_dataset_name,
        test_set_pdk=test_queries_byview, 
        test_set_design=test_design, 
        test_set_interwined=test_queries_interwined,
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
            partition=False,
            load_graph_db=True
        )
    )  

    din_sql = DINSQL(
        config=config
    )

    def answer_pdk(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = din_sql.pdk_agent.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['query']} \n {output['result']}")
        return output

    for key in ["lef"]: 
        pdk_qa_results = evaluate(
            answer_pdk, 
            data=pdk_dataset_name[key],
            experiment_prefix=f"PDK-QA-din-sql-{key}-{model}",
            evaluators=[compute_accuracy],
            max_concurrency=1
        )

        ex = pdk_qa_results._results[0]['evaluation_results']['results'][0].score
        ves = pdk_qa_results._results[0]['evaluation_results']['results'][1].score
        
        logger.info(f"YELLOW: Execution Accuracy (PDK), {ex}, Valid Efficiency Score (PDK), {ves}")

    def answer_design(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = din_sql.design_agent.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['query']} \n {output['result']}")
        return output
    
    design_qa_results = evaluate(
        answer_design, 
        data=design_dataset_name,
        experiment_prefix=f"Design-QA-DIN-SQL-{model}",
        evaluators=[compute_accuracy_cypher],
        max_concurrency=1
    )

    ex = design_qa_results._results[0]['evaluation_results']['results'][0].score
    ves = design_qa_results._results[0]['evaluation_results']['results'][1].score
    
    logger.info(f"YELLOW: Execution Accuracy (DEF), {ex}, Valid Efficiency Score (DEF), {ves}")

    # start_time = time.time()
    # try: 
    #     output = din_sql.forward(
    #        question="How many cells are in the high density library ?"
    #     )
    # except langgraph.errors.GraphRecursionError:
    #     print("Hit Recursion Limit!!")

    # # end_time = time.time()

    # print(f"Run time: {end_time - start_time}")
    # print(output)
    
    # try: 
    #     output = din_sql.design_agent.forward("How many cells are in the design ?")
    #     print(output)
    # except langgraph.errors.GraphRecursionError:
    #     print("Hit Recursion Limit!!")
    
    # for m in output['messages']:
    #     m.pretty_print()



if __name__ == '__main__':
    main()