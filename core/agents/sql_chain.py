"""SQL Chain
"""
import os 
import time
import argparse

import openai
import sqlite3 
import sqlalchemy
from langchain_community.utilities import SQLDatabase

from dotenv import load_dotenv
load_dotenv()

from core.agents.agent import Agent
from core.agents.routers.router import Router 
from core.agents.routers.view_router import View 
from core.agents.selectors.table_selector import SchemaSelector 
from core.agents.generator.sql_generator import Decomposer, cell_variant
from core.agents.refiner import RefinerSQL 
from core.agents.interpreter import Interpreter 
from core.eval.test_set import test_queries, test_queries_lef, test_queries_lib, test_queries_tlef
from core.eval.cases import pdk_cases
from core.eval.metrics import compute_execution_acc, compute_ves
from core.database.sql import get_desc, get_fk, get_table_names
from core.utils import get_logger, parse_qa_pairs, parse_sql_from_string


class SQLChain(Agent):
    
    def __init__(self, model='gpt-3.5-turbo-0125', query_model='gpt-3.5-turbo-0125', temperature=0, few_shot=True,\
                 use_router=True, use_decomposer=True, use_selector=True, use_refiner=True, use_interpreter=True, aux_llm=None, query_llm=None, llm=None, \
                 use_sql_coder_prompt=False, use_vanilla_rag=False, use_din_mac=False ):
        super().__init__()

        self.use_router = use_router 
        self.use_selector = use_selector
        self.use_decomposer = use_decomposer 
        self.use_refiner = use_refiner
        self.use_interpreter = use_interpreter
        self.use_vanilla_rag = use_vanilla_rag
        self.use_din_mac = use_din_mac
        # load the model here once and send it to the agent constructors; 
        if llm: 
            aux_llm = llm 
            query_llm = llm 
        else: 
            aux_llm = self.get_model(
                model=model,
                temperature=temperature,
                structured_output=True
            )
            
            query_llm =  self.get_model(
                model=query_model,
                temperature=temperature,
                structured_output=False
            ) 

        self.router = Router(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=aux_llm
        ) 

        self.selector = SchemaSelector(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm = aux_llm
        )

        self.decomposer = Decomposer(
            few_shot=few_shot, 
            decompose=use_decomposer,
            model=query_model,
            temperature=temperature,
            llm=query_llm,
            use_sql_coder_prompt=use_sql_coder_prompt,
            use_vanilla_prompt=use_vanilla_rag,
            use_din_mac_prompt=use_din_mac
        )

        self.refiner = RefinerSQL(
            model=model,
            temperature=temperature,
            llm=aux_llm
        )

        self.interpreter = Interpreter(
            model='gpt-3.5-turbo-0125',
            temperature=temperature,
            llm=aux_llm
        ) 

    def generate(self, question, database):
        # 1. Run Router  
        if self.use_router: 
            routed_scl_variant, routed_view, query_op_cond = self.router.route(
                query=question
            )
            query_view = routed_view.view
            routed_scl_libraries = routed_scl_variant.get_libraries()
            query_scl = cell_variant(routed_scl_libraries) 
            
            desc_str=get_desc(routed_view.view)
            fk_str=get_fk(routed_view.view)
            view_table_names = get_table_names(query_view)
        else:
            query_view = None
            routed_scl_libraries = ""
            query_scl = ""
            query_op_cond = ""
            
            fk_str = ""
            desc_str = ""
            view_table_names = []
            for view in [v.value for v in View]: 
                desc_str += get_desc(view)
                fk_str += get_fk(view)
                view_table_names += get_table_names(view)


        # 2. Run Selector  
        if self.use_selector: 
            selected_tables = self.selector.select(
                query=question, 
                datasource=query_view, 
                desc_str=desc_str, 
                fk_str=fk_str, 
                table_info=database.get_table_info(table_names=view_table_names), 
            )
            query_tables = selected_tables.get_selected_columns() 
            query_tables_descr = get_desc(query_view, query_tables)
            fk_str = get_fk(query_view, query_tables)
            table_info = database.get_table_info(table_names=query_tables)
        else:
            query_tables = []
            query_tables_descr = ""
            fk_str = ""
            table_info = ""
            query_tables += get_table_names(query_view)
            query_tables_descr += get_desc(query_view, selected_schema=get_table_names(query_view))
            fk_str += get_fk(query_view, selected_schema=get_table_names(query_view))
            table_info += database.get_table_info(table_names=get_table_names(query_view))

        
        # 3. Run Decomposer 
        response = self.decomposer.decompose(
            query=question,
            view=query_view,
            desc_str=query_tables_descr,
            table_info=table_info, 
            fk_str=fk_str,
            scl_variant=query_scl,
            op_cond=query_op_cond
        )
        
        qa_pairs = parse_qa_pairs(response)
        final_sql = parse_sql_from_string(response)

       
        # Execute generated sql and Refine it if errors are detected 
        refined_sql = ""
        if self.use_refiner: 

            refiner_response = self.refiner.execute(
                input=question,
                database=database,
                query=final_sql,
                desc_str=query_tables_descr,
                table_info=table_info,
                fk_str=fk_str,
                scl_variant=query_scl,
                op_cond=query_op_cond
            )

            refined_sql = parse_sql_from_string(refiner_response)
            final_sql = refined_sql 
       
        try: 
            query_result = database.run(final_sql)
        except: 
            query_result= None 
        
        print("Responnse is: ", response)
        print("Final SQL: ", final_sql)
        print("QA Pairs: ", qa_pairs)
        print(query_result)

        # 4. Run Interpreter 
        answer = None
        if self.use_interpreter: 
            answer = self.interpreter.interpret(
                question=question,
                query=final_sql,
                query_result=query_result,
                dialect='SQL',
            )
        
        steps = {
            'routed_scl_libraries': routed_scl_libraries,
            'scl_library': query_scl,
            'query_result': query_result,
            'view': query_view,
            'tables': query_tables, 
            'tables_descr': query_tables_descr,
            'fk_str': fk_str ,
            'table_info': table_info,
            'op_cond': query_op_cond,
            'final_sql': final_sql,
            'qa_pairs': qa_pairs,
            'refined_sql': final_sql,
            'answer': answer    
        }
        
        return steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/sql_chain_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo')
    parser.add_argument('--query_model', type=str, help='Model name used for generating SQL queries')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--wo_decomposer', action='store_true', default=False)
    parser.add_argument('--wo_selector', action='store_true', default=False)
    parser.add_argument('--wo_router', action='store_true', default=False)
    parser.add_argument('--wo_refiner', action='store_true', default=False)
    parser.add_argument('--wo_interpreter', action='store_true', default=False)
    parser.add_argument('--use_sql_coder', action='store_true', default=False)
    parser.add_argument('--run_cases', action='store_true', default=False)
    args = parser.parse_args()
    
    if args.query_model is None:
        args.query_model = args.model
        
    output = args.output 
    model = args.model
    query_model = args.query_model
    few_shot = not args.wo_fewshot
    use_decomposer = not args.wo_decomposer 
    use_refiner = not args.wo_refiner
    use_sql_coder_prompt = args.use_sql_coder
    use_selector = not args.wo_selector
    use_router = not args.wo_router
    use_interpreter = not args.wo_interpreter 

    run_cases = args.run_cases 
  
    sql_chain = SQLChain(
        few_shot=few_shot, 
        use_decomposer=use_decomposer,
        use_router=use_router,
        use_selector=use_selector,
        use_refiner=use_refiner,
        use_interpreter=use_interpreter,
        model=model,
        query_model=query_model,
        temperature=0,
        use_sql_coder_prompt=use_sql_coder_prompt
    )
    
    output = f'./output/sql_chain/{model}.log'
    os.makedirs(os.path.dirname(output), exist_ok=True)

    logger = get_logger(output)
    logger.info(f"BLUE: Auxilary LLM Agent: {model}") 
    logger.info(f"BLUE: SQL-Generator Agent: {query_model}") 
    logger.info(f"BLUE: Few shot set to: {few_shot}") 
    logger.info(f"BLUE: Use selector set to: {use_selector}") 

    database_path = "dbs/sky130.db"
    database = SQLDatabase.from_uri(
        f"sqlite:///{database_path}", 
        view_support=True
    )

    predicted_sqls = []
    predicted_sqls_byview = {'Liberty': [], 'Lef': [], 'TechnologyLef': []}
    
    ground_truth_sqls = []
    ground_truth_sqls_byview = {'Liberty': [], 'Lef': [], 'TechnologyLef': []}

    sql_correct = 0
    sql_correct_byview = {'Liberty': 0, 'Lef': 0, 'TechnologyLef': 0}

    total_time = 0
    test_set = pdk_cases if run_cases else test_queries
    logger.info(f"BLUE: Running Test Set with size {len(test_set)}")
    
    test_set = test_queries_tlef
    for query in test_set: 
        logger.info(f"BLUE: User question is {query['input']}")

        start_time = time.time()
            
        try: 
            result = sql_chain.generate(
                question=query["input"],
                database=database,
                run_interpreter=True,
            )
        except (openai.BadRequestError, TypeError):
            predicted_sqls.append('')
            predicted_sqls_byview[query['view']].append('')
            ground_truth_sqls.append(query['ground_truth'])
            ground_truth_sqls_byview[query['view']].append(query['ground_truth'])
            continue 
        
        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time
    
        query_view = result['view']
        refined_sql = result['refined_sql']

        view_score =  sql_chain.router.view_router.view_metric(query['view'], result['view'])
        color = 'GREEN' if view_score else 'RED'
        logger.info(f"{color}: Routed View: {query_view}")
        logger.info(f"BLUE: Ground Truth View: {query['view']}")

        scl_score = sql_chain.router.scl_router.scl_metric(query['scl_variant'], result['routed_scl_libraries'])
        color = 'GREEN' if scl_score else 'RED'
        logger.info(f"{color}: Routed Cell Library: {result['routed_scl_libraries']}")
        
        logger.info(f"YELLOW: Routed Operating Conditions: {result['op_cond']}")
        
        selector_score =  sql_chain.selector.compute_subset_accuracy(result['tables'], query['selected_tables'])
        color = 'GREEN' if selector_score else 'RED'
        logger.info(f"{color}: Selected Tables: {result['tables']}")
        
        # logger.info(f"BLUE: Table Descriptions: {result['tables_descr']}")
        # logger.info(f"BLUE: Foreign Keys: {result['fk_str']}")

        for pair in result['qa_pairs']: 
            subquestion = pair[0]
            subquery = pair[1]
            logger.info(f"CYAN: Subquestion: {subquestion}")
            logger.info(f"Yellow: Subquery: {subquery}")

        try: 
            acc = compute_execution_acc([refined_sql], [query['ground_truth']], database) 
        except (sqlite3.OperationalError, sqlalchemy.exc.OperationalError) as e:
            logger.info(f"RED: Error {e} during SQL execution")
            acc = 0
            
        sql_correct += acc 
        sql_correct_byview[query['view']]+= acc

        color = 'GREEN' if acc else 'RED'
        logger.info(f"{color}: Final SQL is \n {result['final_sql']}")
        logger.info(f"{color}: Refined SQL is \n  {result['refined_sql']}")
        logger.info(f"BLUE: Ground Truth SQL is \n  {query['ground_truth'][0]}")
        logger.info(f"{color}: Accuracy is {acc}")
        logger.info(f"YELLOW: ***LLM Output is***: \n {result['answer']}")

        predicted_sqls.append(refined_sql)
        predicted_sqls_byview[query['view']].append(refined_sql)

        ground_truth_sqls.append(query["ground_truth"])
        ground_truth_sqls_byview[query['view']].append(query["ground_truth"])

        break 
       
    num_iters = 3 
    ex = compute_execution_acc(predicted_sqls, ground_truth_sqls, database)
    ves = compute_ves(predicted_sqls, ground_truth_sqls, database, num_iters=num_iters)
    logger.info(f"WHITE: Overall Execution Accuracy {ex}, Overall Valid Efficiency Score {ves}")
    
    # break down accuracy by view
    ex_lib = compute_execution_acc(predicted_sqls_byview['Liberty'], ground_truth_sqls_byview['Liberty'], database)
    ves_lib = compute_ves(predicted_sqls_byview['Liberty'], ground_truth_sqls_byview['Liberty'], database, num_iters=num_iters)
    logger.info(f"WHITE: Lib Execution Accuracy {ex_lib}, Lib Valid Efficiency Score {ves_lib}")

    ex_lef = compute_execution_acc(predicted_sqls_byview['Lef'], ground_truth_sqls_byview['Lef'], database)
    ves_lef = compute_ves(predicted_sqls_byview['Liberty'], ground_truth_sqls_byview['Liberty'], database, num_iters=num_iters)
    logger.info(f"WHITE: LEF Execution Accuracy {ex_lef}, LEF Valid Efficiency Score {ves_lef}")

    ex_tlef = compute_execution_acc(predicted_sqls_byview['TechnologyLef'], ground_truth_sqls_byview['TechnologyLef'], database)
    ves_tlef = compute_ves(predicted_sqls_byview['TechnologyLef'], ground_truth_sqls_byview['TechnologyLef'], database, num_iters=num_iters)
    logger.info(f"WHITE: TechLef Execution Accuracy {ex_tlef}, TechLef Valid Efficiency Score {ves_tlef}")

    # average QA time
    average_time = total_time / len(test_queries)
    logger.info(f"WHITE: Average time per query: {average_time:.2f} seconds")
    
    
    
if __name__ == '__main__':
    main()
    