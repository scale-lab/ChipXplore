"""Main entry point for the framework
"""

import os 
import time 

import json
import neo4j
import sqlite3
import sqlalchemy
import argparse

import openai
import ollama
from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities import SQLDatabase

from core.utils import get_logger
from core.agents.cypher_chain import CypherChain 
from core.agents.sql_chain import SQLChain 
from core.agents.agent import Agent
from core.agents.planner import ReActQueryPlanner 
from core.agents.routers.db_router import DatabaseRouter
from core.eval.test_graph import test_design
from core.eval.test_set import test_queries, test_queries_lef, test_queries_lib, test_queries_tlef
from core.eval.test_design_pdk import test_design_pdk
from core.eval.cases import pdk_cases, design_cases, pdk_design_cases
from core.eval.metrics import compute_execution_acc, compute_ves
from core.database.graphdb import URI, USER, PASSWORD, get_node_descr


class ChipQuery(Agent):
    
    def __init__(self, model, temperature=0, use_planner=True, use_router=True, use_selector=True, use_decomposer=True, use_refiner=True, use_interpreter=False, use_vanilla_rag=False, use_din_mac=False) -> None:
        # Agents
        super().__init__()
        
        self.use_planner = use_planner
        self.use_router = use_router 
        self.use_selector = use_selector 
        self.use_decomposer = use_decomposer
        self.use_refiner = use_refiner 
        self.use_interpreter = use_interpreter 
        self.use_vanilla_rag = use_vanilla_rag 
        self.use_din_mac = use_din_mac

        llm = self.get_model(
            model=model,
            temperature=temperature
        )

        self.db_router = DatabaseRouter(
            model=model,
            temperature=temperature,
            llm=llm
        )

        self.planner = ReActQueryPlanner(
            model=model,
            temperature=temperature,
            llm=llm
        )

        self.cypher_chain = CypherChain(
            model=model,
            temperature=temperature,
            few_shot=True,
            llm=llm,
            use_selector=use_selector,
            use_router=use_router,
            use_decomposer=use_decomposer,
            use_refiner=use_refiner,
            use_interpreter=use_interpreter,
            use_vanilla_rag=use_vanilla_rag,
            use_din_mac=use_din_mac
        )

        self.sql_chain = SQLChain(
            model=model,
            query_model=model,
            temperature=temperature,
            few_shot=True,
            llm=llm,
            use_router=use_router,
            use_selector=use_selector,
            use_decomposer=use_decomposer,
            use_refiner=use_refiner,
            use_interpreter=use_interpreter,
            use_vanilla_rag=use_vanilla_rag,
            use_din_mac=use_din_mac
        )

        # Databases 
        self.sql_database = SQLDatabase.from_uri(
            f"sqlite:///dbs/sky130.db", 
            view_support = True
        )

        self.graph_database = Neo4jGraph(
            url=URI, 
            username=USER, 
            password=PASSWORD, 
            database='sky130',
            enhanced_schema=True
        ) 
        self.graph_database.refresh_schema()
     
    def answer(self, question):
        
        out = self.db_router.route(query=question)
        database = out.get_databases()
        
        output = dict()
        output['routed_database'] = database 

        if set(database) == set(['pdk', 'design']): 
            output = self.planner.plan_and_execute(
                user_query=question,
                sql_chain=self.sql_chain,
                cypher_chain=self.cypher_chain,
                sql_database=self.sql_database,
                graph_database=self.graph_database,
            ) 
            if 'error' in output.keys():
                output['routed_database'] = database
                return output 
            response = output['answer']
        elif set(database) == set(['pdk']): 
            output = self.sql_chain.generate(
                question=question,
                database=self.sql_database,
            )
            response = output['answer']
        elif set(database) == set(['design']):
            output = self.cypher_chain.generate(
                question=question, 
                database=self.graph_database
            )
            response = output['answer']
        else:
            response = f"Invalid database type: {database}"
        
        output['response'] = response
        output['routed_database'] = database
        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default=None)
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_planner',  help='Run without planner agent, use one-shot', action='store_true', default=False)
    parser.add_argument('--wo_router',  help='Run without router agent', action='store_true', default=False)
    parser.add_argument('--wo_selector',  help='Run without selector agent', action='store_true', default=False)
    parser.add_argument('--wo_decomposer',  help='Run without query decomposition', action='store_true', default=False)
    parser.add_argument('--wo_refiner',  help='Run without refiner', action='store_true', default=False)
    parser.add_argument('--wo_interpreter',  help='Run without interpreter', action='store_true', default=False)
    parser.add_argument('--use_vanilla_rag',  help='Run with vanilla RAG prompt', action='store_true', default=False)
    parser.add_argument('--use_din_mac',  help='Run with DIN-MAC SQL prompt', action='store_true', default=False)
    parser.add_argument('--run_cases', action='store_true', default=False)
    parser.add_argument('--run_techlef',  help='Runs techlef queries only', action='store_true', default=False)
    parser.add_argument('--run_lef',  help='Runs lef queries only', action='store_true', default=False)
    parser.add_argument('--run_lib',  help='Runs lib queries only', action='store_true', default=False)
    parser.add_argument('--run_def',  help='Runs def queries only', action='store_true', default=False)
    args = parser.parse_args()
    
    model = args.model
    output = args.output 
    use_planner = not args.wo_planner 
    use_router = not args.wo_router 
    use_selector = not args.wo_selector
    use_decomposer = not args.wo_decomposer 
    use_refiner = not args.wo_refiner 
    use_interpreter = not args.wo_interpreter 
    use_vanilla_rag = args.use_vanilla_rag
    use_din_mac = args.use_din_mac
    run_cases = args.run_cases 
    run_techlef = args.run_techlef 
    run_lef = args.run_lef 
    run_lib = args.run_lib 
    run_def = args.run_def
    run_all = not (run_techlef or run_lef or run_def or run_lib)
    
    if output is None: 
        if run_cases: 
            output = f'output/chipquery/cases/{model}.log'
        elif run_all: 
            output = f'output/chipquery/{model}/{model}.log'
        elif run_techlef: 
            output = f'output/chipquery/{model}/{model}_techlef.log'
        elif run_lef:
            output = f'output/chipquery/{model}/{model}_lef.log'
        elif run_lib:
            output = f'output/chipquery/{model}/{model}_lib.log'
        elif run_def:
            output = f'output/chipquery/{model}/{model}_def.log'

    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    
    chip_query = ChipQuery(
        model=model,
        temperature=0,
        use_planner=use_planner,
        use_router=use_router,
        use_selector=use_selector,
        use_decomposer=use_decomposer,
        use_refiner=use_refiner,
        use_interpreter=use_interpreter,
        use_vanilla_rag=use_vanilla_rag,
        use_din_mac=use_din_mac
    ) 
    
    logger = get_logger(output)
    logger.info(f"CYAN: LLM Agent is {model}") 
    logger.info(f"CYAN: Use Router {use_router}, \
                Use Selector {use_selector}, \
                Use Decomposer {use_decomposer},  Use Refiner {use_refiner}.") 

    predicted_queries = []
    predicted_queries_byview = {
        'Liberty': [], 
        'Lef': [], 
        'TechnologyLef': [], 
        'DEF': []
    }
    
    ground_truth_queries = []
    ground_truth_queries_byview = {
        'Liberty': [], 
        'Lef': [], 
        'TechnologyLef': [], 
        'DEF': []
    }
    
    total_time = 0
   
    # test PDK questions
    if run_cases:
        test_set = pdk_cases 
    elif run_all:
        test_set = test_queries 
    elif run_techlef:
        test_set = test_queries_tlef 
    elif run_lef:
        test_set = test_queries_lef 
    elif run_lib:
        test_set = test_queries_lib 
    else:
        test_set = []
    
    for query in test_set: 
        logger.info(f"CYAN: User question is {query['input']}")
        
        try: 
            start_time = time.time()
            result = chip_query.answer(question=query['input'])
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
        except (openai.BadRequestError, TypeError, KeyError, AttributeError, json.decoder.JSONDecodeError) as e:
            logger.info(f"Error {e}, !!!")
            predicted_queries.append('')
            predicted_queries_byview[query['view']].append('')
            ground_truth_queries.append(query['ground_truth'])
            ground_truth_queries_byview[query['view']].append(query['ground_truth'])
            continue 
        
        # if 'error' in result.keys():
        #     logger.info(f"Error {result['error']}, !!!")
        #     predicted_queries.append('')
        #     predicted_queries_byview[query['view']].append('')
        #     ground_truth_queries.append(query['ground_truth'])
        #     ground_truth_queries_byview[query['view']].append(query['ground_truth'])
        #     continue 

        if 'error' in result.keys() or set(result['routed_database']) != set(['pdk']) :
            predicted_queries.append('')
            predicted_queries_byview[query['view']].append('')
        
            ground_truth_queries.append(query['ground_truth'])
            ground_truth_queries_byview[query['view']].append(query['ground_truth'])
            print("Encountered an error, ")
            continue 
        
        query_view = result['view']
        refined_sql = result['refined_sql']

        db_score = set(result['routed_database']) == set(['pdk'])
        color = 'GREEN' if db_score else 'RED'
        logger.info(f"{color}: Routed Database, {result['routed_database']}")
        
        view_score =  chip_query.sql_chain.router.view_router.view_metric(query['view'], result['view'])
        color = 'GREEN' if view_score else 'RED'
        logger.info(f"{color}: Routed View, {query_view}")
        logger.info(f"BLUE: Ground Truth View, {query['view']}")

        scl_score = chip_query.sql_chain.router.scl_router.scl_metric(query['scl_variant'], result['routed_scl_libraries'])
        color = 'GREEN' if scl_score else 'RED'
        logger.info(f"{color}: Routed Cell Library, {result['routed_scl_libraries']}")

        logger.info(f"YELLOW: Routed Operating Conditions, {result['op_cond']}")
        
        selector_score =  chip_query.sql_chain.selector.compute_subset_accuracy(result['tables'], query['selected_tables'])
        color = 'GREEN' if selector_score else 'RED'
        logger.info(f"{color}: Selected Tables, {result['tables']}")
        
        for pair in result['qa_pairs']: 
            subquestion = pair[0]
            subquery = pair[1]
            logger.info(f"CYAN: Subquestion, {subquestion}")
            logger.info(f"MAGENTA: Subquery, {subquery}")
        
        try: 
            acc = compute_execution_acc([refined_sql], [query['ground_truth']], chip_query.sql_database) 
        except (sqlite3.OperationalError, sqlalchemy.exc.OperationalError) as e:
            logger.info(f"RED: Error {e} during SQL execution")
            acc = 0

        color = 'GREEN' if acc else 'RED'
        logger.info(f"{color}: Final SQL is \n {result['final_sql']}")
        logger.info(f"{color}: Refined SQL is \n  {result['refined_sql']}")
        logger.info(f"BLUE: Ground Truth SQL is \n  {query['ground_truth'][0]}")
        logger.info(f"{color}: Accuracy is {acc}")

        predicted_queries.append(result['refined_sql'])
        predicted_queries_byview[query['view']].append(result['refined_sql'])
        
        ground_truth_queries.append(query['ground_truth'])
        ground_truth_queries_byview[query['view']].append(query['ground_truth'])

        if 'steps' in result.keys(): 
            for step in result['steps']:
                logger.info(f"BLUE: Step {step['id']} \n {step['thought']}")
                logger.info(f"YELLOW: Action, {step['action']}")
                logger.info(f"YELLOW: Action inputs, {step['action_input']}")
                if 'result' in step.keys(): 
                    logger.info(f"MAGENTA: {step['result']}")

        
        logger.info(f"YELLOW: ***LLM Output is***: \n {result['answer']}")
        logger.info(f"CYAN: ***Answer Time***: {query_time}")

    
    num_iters = 3 
    ex = compute_execution_acc(predicted_queries, ground_truth_queries, chip_query.sql_database)
    ves = compute_ves(predicted_queries, ground_truth_queries, chip_query.sql_database, num_iters=num_iters)
    logger.info(f"WHITE: Overall Execution Accuracy {ex}, Overall Valid Efficiency Score {ves}")
    
    print("Predicted QUeries are: ", predicted_queries)
    print("Predicted QUeries by view are: ", predicted_queries_byview)

    print("GT QUeries are: ", ground_truth_queries)
    print("GT QUeries by view are: ", ground_truth_queries_byview)

    # break down accuracy by view
    ex_lib = compute_execution_acc(
        predicted_queries=predicted_queries_byview['Liberty'], 
        ground_truth_queries=ground_truth_queries_byview['Liberty'], 
        db_path=chip_query.sql_database
    )
    ves_lib = compute_ves(
        predicted_queries=predicted_queries_byview['Liberty'], 
        ground_truth=ground_truth_queries_byview['Liberty'], 
        db_path=chip_query.sql_database, 
        num_iters=num_iters
    )
    logger.info(f"WHITE: Lib Execution Accuracy {ex_lib}, Lib Valid Efficiency Score {ves_lib}")

    ex_lef = compute_execution_acc(
        predicted_queries=predicted_queries_byview['Lef'], 
        ground_truth_queries=ground_truth_queries_byview['Lef'], 
        db_path=chip_query.sql_database
    )
    ves_lef = compute_ves(
        predicted_queries=predicted_queries_byview['Liberty'], 
        ground_truth=ground_truth_queries_byview['Liberty'], 
        db_path=chip_query.sql_database, 
        num_iters=num_iters
    )
    logger.info(f"WHITE: LEF Execution Accuracy {ex_lef}, LEF Valid Efficiency Score {ves_lef}")

    ex_tlef = compute_execution_acc(
        predicted_queries=predicted_queries_byview['TechnologyLef'], 
        ground_truth_queries=ground_truth_queries_byview['TechnologyLef'], 
        db_path=chip_query.sql_database
    )
    ves_tlef = compute_ves(
        predicted_queries=predicted_queries_byview['TechnologyLef'], 
        ground_truth=ground_truth_queries_byview['TechnologyLef'], 
        db_path=chip_query.sql_database, 
        num_iters=num_iters
    )
    logger.info(f"WHITE: TechLef Execution Accuracy {ex_tlef}, TechLef Valid Efficiency Score {ves_tlef}")

    # average QA time
    if len(test_set) != 0: 
        average_time = total_time / len(test_set)
        logger.info(f"WHITE: Average time per query: {average_time:.2f} seconds")
        
    # # test design questions 
    total_time = 0
    predicted_queries = []
    ground_truth_queries = []
    
    if run_cases: 
        test_set = design_cases 
    elif run_all or run_def:
        test_set = test_design 
    else:
        test_set = []
    
    for query in test_set: 
        logger.info(f"CYAN: User question is {query['input']}")
        try: 
            start_time = time.time()
            result = chip_query.answer(question=query['input'])
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
        except (openai.BadRequestError, IndexError, neo4j.exceptions.CypherSyntaxError, ValueError, ollama._types.ResponseError):
            predicted_queries.append('')
            predicted_queries_byview['DEF'].append('')
            ground_truth_queries.append(query['ground_truth'])
            ground_truth_queries_byview['DEF'].append(query['ground_truth']) 
            continue 
        
        # if 'error' in result.keys() or 'stage' not in result.keys():
        #     predicted_queries.append('')
        #     predicted_queries_byview['DEF'].append('')
        #     ground_truth_queries.append(query['ground_truth'])
        #     ground_truth_queries_byview['DEF'].append(query['ground_truth'])
        #     continue 
        
        
        if 'error' in result.keys() or set(result['routed_database']) != set(['design']) :
            predicted_queries.append('')
            predicted_queries_byview['DEF'].append('')
        
            ground_truth_queries.append(query['ground_truth'])
            ground_truth_queries_byview['DEF'].append(query['ground_truth'])
            continue 

        stage_score =  chip_query.cypher_chain.router.stage_metric(query['stage'], result['stage'])
        color = 'GREEN' if stage_score else 'RED'
        logger.info(f"{color}: Routed Stage {result['stage']}")
        logger.info(f"BLUE: Ground Truth Stage {query['stage']}")

        node_score = chip_query.cypher_chain.selector.compute_subset_accuracy(result['selected_nodes'], query['selected_nodes'])
        color = 'GREEN' if node_score else 'RED'
        logger.info(f"{color}: Selected Nodes, {result['selected_nodes']}")
        
        for pair in result['qa_pairs']: 
            subquestion = pair[0]
            subquery = pair[1]
            logger.info(f"CYAN: Subquestion, {subquestion}")
            logger.info(f"MAGENTA: Subquery, {subquery}")
    
        refined_cypher = result['refined_cypher']
        try: 
            acc = compute_execution_acc([refined_cypher], [query['ground_truth']], chip_query.graph_database, use_cypher=True) 
        except:
            acc = 0 
            
        predicted_queries.append(result['refined_cypher'])
        predicted_queries_byview['DEF'].append(result['refined_cypher'])
        
        ground_truth_queries.append(query['ground_truth'])
        ground_truth_queries_byview['DEF'].append(query['ground_truth'])
    
        color = 'GREEN' if acc else 'RED'
        logger.info(f"{color}: Final Cypher is \n {result['cypher_query']}")
        logger.info(f"{color}: Refined Cypher is \n  {result['refined_cypher']}")
        logger.info(f"BLUE: Ground Truth Cypher is \n  {query['ground_truth'][0]}")
        logger.info(f"{color}: Accuracy is {acc}")

        if 'steps' in result.keys(): 
            for step in result['steps']:
                logger.info(f"BLUE: Step {step['id']} \n {step['thought']}")
                logger.info(f"YELLOW: Action: {step['action']}")
                logger.info(f"YELLOW: Action inputs: {step['action_input']}")
                if 'result' in step.keys(): 
                    logger.info(f"MAGENTA: {step['result']}")
        
        logger.info(f"YELLOW: ***LLM Output is***: \n {result['answer']}")
        logger.info(f"CYAN: ***Answer Time***:  {query_time}")
        
    num_iters = 3 
    ex = compute_execution_acc(predicted_queries, ground_truth_queries, chip_query.graph_database, use_cypher=True)
    ves = compute_ves(predicted_queries, ground_truth_queries, chip_query.graph_database, num_iters=num_iters, use_cypher=True)
    logger.info(f"WHITE: DEF Execution Accuracy {ex}, DEF Valid Efficiency Score {ves}")
    
    # average QA time
    if len(test_set) != 0: 
        average_time = total_time / len(test_set)
        logger.info(f"WHITE: Average time per query: {average_time:.2f} seconds")
    
    
    # # test design-pdk questions 
    # test_set = pdk_design_cases if run_cases else test_design_pdk
    # for query in test_set: 
    #     logger.info(f"CYAN: User question is {query['input']}")

    #     start_time = time.time()
    #     result = chip_query.answer(question=query['input'])
    #     end_time = time.time()
    #     query_time = end_time - start_time
    #     total_time += query_time

    #     if 'steps' in result.keys(): 
    #         for step in result['steps']:
    #             logger.info(f"BLUE: Step {step['id']} \n {step['thought']}")
    #             logger.info(f"YELLOW: Action: {step['action']}")
    #             logger.info(f"YELLOW: Action inputs: {step['action_input']}")
    #             if 'result' in step.keys(): 
    #                 logger.info(f"MAGENTA: {step['result']}")
    
    #     logger.info(f"YELLOW: ***LLM Output is***: \n {result['answer']}")
    #     logger.info(f"CYAN: ***Answer Time***: {query_time}")


if __name__ == '__main__':
    main()