"""
    Verify Generated SQL/Cypher Queries
"""

import os 
import sqlite3
import argparse
import sqlalchemy

from core.utils import get_logger
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig


class Verifier:

    def __init__(self, config, dialect, logger) -> None:
        self.config = config
        self.dialect = dialect 
        self.logger = logger 

    def verify(self, query):
        correct = False 
        try: 
            if self.dialect == 'SQL': 
                result = self.config.db_config.pdk_database.run(query)
            elif self.dialect == 'Cypher': 
                result = self.config.db_config.design_database.run(query)
            if result:
                correct = True 
        except (sqlite3.OperationalError, sqlalchemy.exc.OperationalError) as e:
            self.logger.info(f"RED: Query {query} is invalid, Got Error {e}")
        
        return correct

    def filter(self, queries, questions, results):
        filtered_questions = []
        filtered_queries = [] 
        filtered_results = []

        for question, query, result in  zip(questions, queries, results):
            ### TODO: USE another LLM as a judge to check that 
            ### the generated query answers the questions correctly
            if self.verify(query): 
                filtered_questions.append(question)
                filtered_queries.append(query)
                filtered_results.append(result)
            else:
                self.logger.info(f"RED: Skipping query {query} because reuslt is empty...")
    
        return filtered_questions, filtered_queries, filtered_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--dialect', type=str, help='Query dialect', default='SQL')
    parser.add_argument('--output', type=str, help='Path to output directory', default='./output/')
    args = parser.parse_args()
 
    model = args.model 
    dialect = args.dialect
    output = args.output

    output_dir = os.path.join(output, f'{dialect}_dataset')
    os.makedirs(output_dir, exist_ok=True)

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=True,
            secure=False,
            graph_recursion_limit=15,
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=model,
        ),
        db_config=DatabaseConfig(
            partition=False,
            in_mem_db=True,
            load_graph_db=False
        ),
    )

    questions = [
        "How many cells are in the high speed library ? ",
        "How many cells are in the high speed library ? ",
        "How many cells are in the high speed library ? ",
    ]

    queries = [
        "SELECT COUNT(*) FROM",
        "SELECT COUNT(*) FROM",
        "SELECT COUNT(*) FROM",
    ]


    logger = get_logger(os.path.join(output, f'{dialect}_verifier.log'))

    verifier = Verifier(
        config=config,
        logger=logger
    )
    
    filtered_questions, filtered_queries = verifier.filter(
        questions=questions,
        queries=queries,
        dialect='SQL'
    )

    logger.info(f"YELLOW: Filtered Queries, {filtered_queries}")
    logger.info(f"YELLOW: Filtered Questions, {filtered_questions}")



if __name__ == '__main__':
    main()