"""ReAct style agent, Query Planner
"""
import os 
import time
import json
import argparse 
from enum import Enum
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate

from core.utils import get_logger
from core.agents.cypher_chain import CypherChain 
from core.agents.sql_chain import SQLChain 
from core.agents.interpreter import Interpreter
from core.agents.agent import Agent 

from core.eval.test_graph import test_design
from core.eval.test_set import test_queries
from core.eval.test_design_pdk import test_design_pdk
from core.eval.metrics import compute_execution_acc, compute_ves
from core.database.graphdb import URI, USER, PASSWORD, get_node_descr
from core.database.sql import get_desc 

from dotenv import load_dotenv
load_dotenv()


PLANNER_SYS_PROMPT = """
You are an AI assistant specializing in semiconductor design and process design kits (PDKs). 
Your task is to determine whether to directly query a database or to create and execute a query plan to answer user question.

You have access to two chains:
1. PDK Chain: Retrieves information from the PDK database such as information about the process design kit, including standard cell libraries, library views, and operating conditions. 
[NOTE]: 
    - Cell names in the PDK are prefixed with library.
    - For example cells in high density are prefixed with 'sky130_fd_sc_hd__'. 
    - High speed are prefixed with 'sky130_fd_sc_hs__'. 
    - High density low leakage are prefixed with 'sky130_fd_sc_hdll__'
    - When querying the PDK chain for information about a specific cell, make sure the cell name prefix matches the library. 
    
2. Design Chain: Retrieves information from the design database such as information cell instances, nets, pins, and design-specific metrics.

Each step in a plan should be one of two actions:
1. 'database_query': For querying either the PDK or Design chains
2. 'finish':  When you have the final answer to the user's question

Format your response as a JSON object with the following fields:
- 'thought': Your reasoning about the current state and what to do next
- 'action': The type of action to take ('database_query', or 'finish')
- 'action_input': A dictionary containing details about the action:
  - For 'database_query': 
        - 'target_db' (either 'pdk_db' or 'design_db')
        - 'question' Question for this database to retrieve relevant information
  - For 'finish': 
        - 'thought': your thoughts on how to formulate the final answer to the user question
        - 'answer' the final answer to the user's question

[Requirements]
- If the question requires querying both databases, create a detailed plan to handle subqueries and combining results.

Previous steps and their results:
{previous_steps}

Your plan must adhere to the requirements and covers all necessary steps to fully answer the question: 
{user_question}

"""


class ReActQueryPlanner(Agent):
    """Plans and executes actions for complex user questions that require cross-database queries."""
    def __init__(self, model, temperature=0, llm=None):
        super().__init__()
        self.system_prompt = PLANNER_SYS_PROMPT
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{user_question}")
        ])
        self.model = model 
        if llm:
            self.llm = llm 
        else: 
            self.llm = self.get_model(
                model=model,
                temperature=temperature,
                structured_output=False
            )
            
    def plan_and_execute(self, user_query, sql_chain, cypher_chain, sql_database, graph_database):
        previous_steps = []
        step_counter = 1
        
        planner = self.prompt | self.llm 
        
        sql_result = None 
        cypher_result = None 
        while True:
            # Generate the next step
            response = planner.invoke({
                'user_question': user_query,
                'previous_steps': json.dumps(previous_steps, indent=2)
            })
            
            print("Response is: ", response)
            try:
                step = json.loads(response.content)
            except json.JSONDecodeError as e:
                print(f"Error {e}: Invalid JSON response from LLM. Raw response: {response.content}")
                step_counter += 1
                if step_counter >= 5: 
                    break 
                continue
                        
            # Add step ID and append to previous steps
            step['id'] = f'step{step_counter}'
            step_counter += 1
            
            if step['action'] == 'database_query':
                database_type = step['action_input']['target_db']
                subquestion = step['action_input']['question']
                if database_type == 'design_db':
                    cypher_result = cypher_chain.generate(
                        question=subquestion, 
                        database=graph_database, 
                    ) 
                    result = f"""Generated cypher query is {cypher_result['refined_cypher']} \n Query result is {cypher_result['query_result']}"""
                    step['query'] = cypher_result['cypher_query']
                elif database_type == 'pdk_db':
                    subquestion = step['action_input']['question']
                    # print("Subquestion is: ", subquestion)
                    sql_result = sql_chain.generate(
                        question=subquestion,
                        database=sql_database,
                    ) 
                    result = f"""Generated SQL query is {sql_result['refined_sql']} \n Query result is {sql_result['query_result']}"""
                    step['query'] = sql_result['refined_sql']
                else:
                    result = "Invalid database type, it should be design_db or pdk_db."
                    
                step['result'] = result
            elif step['action'] == 'finish':
                
                previous_steps.append(step)
                output = {
                    'answer': step['action_input']['answer'],
                    'steps': previous_steps
                }
                if sql_result:
                    for key in sql_result.keys():
                        output[key] = sql_result[key]
                
                if cypher_result:
                    for key in cypher_result.keys():
                        output[key] = cypher_result[key]
                return output 
            else:
                print(f"Error: Unknown action type '{step['action']}'")
                continue

            previous_steps.append(step)
            # print(step)

            if step_counter >= 5: 
                break 
        return {'error': 'Maximum iterations reached without finishing'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/planner_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    args = parser.parse_args()
    
    model = args.model
    output = args.output 
    
    logger = get_logger(output)
    logger.info(f"CYAN: LLM Agent is {model}") 

    database_path = "dbs/sky130.db"
    sql_database = SQLDatabase.from_uri(
        f"sqlite:///{database_path}", 
        view_support = True
    )

    graph_database = Neo4jGraph(
        url=URI, 
        username=USER, 
        password=PASSWORD, 
        database='sky130',
        enhanced_schema=True
    ) 
    
    query_planner = ReActQueryPlanner(
        model=model,
        temperature=0
    )
    
    cypher_chain = CypherChain(
        model=model,
        temperature=0,
        few_shot=True,
        use_selector=True
    )
    
    sql_chain = SQLChain(
        model=model,
        query_model=model,
        temperature=0,
        few_shot=True,
        decompose=True,
        use_selector=True
    )
    
    interpreter = Interpreter(
        model=model,
        temperature=0
    )
    
    predicted_queries = []
    predicted_queries_byview = {'Liberty': [], 'Lef': [], 'TechnologyLef': [], 'DEF': []}
    
    ground_truth_queries = []
    ground_truth_queries_byview = {'Liberty': [], 'Lef': [], 'TechnologyLef': [], 'DEF': []}
    
    total_time = 0
    for query in test_queries: 
        logger.info(f"BLUE: User question is {query['input']}")

        start_time = time.time()
        output = query_planner.plan_and_execute(
            user_query=query['input'],
            sql_chain=sql_chain,
            cypher_chain=cypher_chain,
            sql_database=sql_database,
            graph_database=graph_database,
        )
        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time
        
        for step in output['steps']:
            logger.info(f"BLUE: Step {step['id']} \n Thought: {step['thought']}")
            logger.info(f"YELLOW: Action: {step['action']}")
            logger.info(f"YELLOW: Action inputs: {step['action_input']}")
            if 'result' in step.keys(): 
                logger.info(f"MAGENTA: {step['result']}")

            if 'query' in step.keys(): 
                predicted_queries.append(step['query'])
                predicted_queries_byview[query['view']].append(step['query'])

        logger.info(f"YELLOW: ***LLM Output is***: \n {output['answer']}")
        ground_truth_queries.append(query['ground_truth'])
        ground_truth_queries_byview[query['view']].append(query["ground_truth"])

    
    num_iters = 3 
    ex = compute_execution_acc(predicted_queries, ground_truth_queries, sql_database)
    ves = compute_ves(predicted_queries, ground_truth_queries, sql_database, num_iters=num_iters)
    logger.info(f"WHITE: Overall Execution Accuracy {ex}, Overall Valid Efficiency Score {ves}")
    
    # break down accuracy by view
    ex_lib = compute_execution_acc(predicted_queries_byview['Liberty'], ground_truth_queries_byview['Liberty'], sql_database)
    ves_lib = compute_ves(predicted_queries_byview['Liberty'], ground_truth_queries_byview['Liberty'], sql_database, num_iters=num_iters)
    logger.info(f"WHITE: Lib Execution Accuracy {ex_lib}, Lib Valid Efficiency Score {ves_lib}")

    ex_lef = compute_execution_acc(predicted_queries_byview['Lef'], ground_truth_queries_byview['Lef'], sql_database)
    ves_lef = compute_ves(predicted_queries_byview['Liberty'], ground_truth_queries_byview['Liberty'], sql_database, num_iters=num_iters)
    logger.info(f"WHITE: LEF Execution Accuracy {ex_lef}, LEF Valid Efficiency Score {ves_lef}")

    ex_tlef = compute_execution_acc(predicted_queries_byview['TechnologyLef'], ground_truth_queries_byview['TechnologyLef'], sql_database)
    ves_tlef = compute_ves(predicted_queries_byview['TechnologyLef'], ground_truth_queries_byview['TechnologyLef'], sql_database, num_iters=num_iters)
    logger.info(f"WHITE: TechLef Execution Accuracy {ex_tlef}, TechLef Valid Efficiency Score {ves_tlef}")

    ex_tlef = compute_execution_acc(predicted_queries_byview['DEF'], ground_truth_queries_byview['DEF'], graph_database)
    ves_tlef = compute_ves(predicted_queries_byview['DEF'], ground_truth_queries_byview['DEF'], graph_database, num_iters=num_iters)
    logger.info(f"WHITE: DEF Execution Accuracy {ex_tlef}, DEF Valid Efficiency Score {ves_tlef}")

    # average QA time
    average_time = total_time / len(test_queries)
    logger.info(f"WHITE: Average time per query: {average_time:.2f} seconds")
    

if __name__ == '__main__':
    main()