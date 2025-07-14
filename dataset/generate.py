"""Generate Synthetic dataset for SQL and Cypher Finetuning 
"""
import os
import re
import json
import sqlite3
import argparse 
import sqlalchemy
from collections import Counter


from core.utils import get_logger
from dataset.model import GPTModel
from config.sky130 import View
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.database.sql import get_desc, get_table_names
from core.graph_flow.pdk_flow import PDKGraph
from core.graph_flow.design_flow import DesignGraph
from dataset_utils import unpack_questions, process_subtopics, merge_subtopics, write_json, count_stats

from dataset.verifier import Verifier
from dataset.question_generator import QuestionGenerator 
from dataset.subtopic_generator import SubTopicGenerator
from dataset.subtopics.subtopics import SUBTOPICS_BYVIEW
from dataset.subtopics.lef_subtopics import LEF_SUBTOPICS 
from dataset.subtopics.tlef_subtopics import TECHLEF_SUBTOPICS 
from dataset.subtopics.lib_subtopics import LIB_SUBTOPICS 
from dataset.subtopics.def_subtopics import DEF_SUBTOPICS 



class QueryGenerator:
    
    def __init__(self, config, model_name, logger, dialect='SQL') -> None:
        self.dialect = dialect
        self.config = config
        self.logger = logger

        self.model = GPTModel(
            name=model_name,
        )

        if dialect == 'SQL':
            self.query_chain = PDKGraph(
               config=config,
               use_interpreter=False
            )
        elif dialect == 'Cypher':
            self.query_chain = DesignGraph(
                config=config,
            )
        else: 
            print(f"[ERROR] Invalid dialect {dialect}")
        
        self.question_generator = QuestionGenerator(
            model_name=model_name
        )

        self.topic_generator = SubTopicGenerator(
            model_name=model_name
        )

        self.verifiter = Verifier(
            config=config,
            dialect=dialect,
            logger=logger
        )


    def generate(self, view, schema, table_descr, subtopics, json_path, num_subtopics=3, num_questions=10):        
        # if num_subtopics > 0: 
        #     generated_subtopics = self.topic_generator.generate(
        #         dialect=self.dialect,
        #         schema=schema, 
        #         table_descr=table_descr, 
        #         num_subtopics=num_subtopics
        #     ) 

        #     subtopics = merge_subtopics(subtopics, generated_subtopics)
            
        #     print(subtopics)
        #     import sys 
        #     sys.exit(0)
         
     
        for subtopic in subtopics:
            self.logger.info(f"BLUE: Generating {num_questions} questions for topic \n {subtopic['name']}")

            generated_questions = []
            generated_queries = []
            generated_results = []

            questions = self.question_generator.generate(
                dialect=self.dialect,
                schema=schema, 
                table_descr=table_descr, 
                subtopic=subtopic, 
                num_questions=num_questions
            ) 

            for _, question in questions.items(): 
                self.logger.info(f"MAGENTA: Topic is {subtopic} \n Qusestion \n {question}")
                
                result = self.query_chain.forward(
                    {"question": question} 
                ) 
                query = result['refined_query']
              
                generated_questions.append(question)
                generated_results.append(result)
                generated_queries.append(query)
                
                self.logger.info(f"Yellow: Generated {self.dialect} Query \n {query}")

            filtered_questions, filtered_queries, filtered_results = self.verifiter.filter(
                questions=generated_questions, 
                queries=generated_queries,
                results=generated_results
            )
            
            write_json(
                topic=subtopic,
                questions=filtered_questions,
                queries=filtered_queries,
                results=filtered_results,
                json_path=json_path
            )
            
            for question, query in zip(filtered_questions, filtered_queries):
                self.logger.info(f"BLUE: Question {question}")
                self.logger.info(f"YELLOW: Query {query}")
                    
        return filtered_questions, filtered_queries
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-4o-mini-2024-07-18')
    parser.add_argument('--dialect', type=str, help='Query dialect', default='SQL')
    parser.add_argument('--num_subtopics', type=int, help='Number of subtopics', default=3)
    parser.add_argument('--num_questions', type=int, help='Number of questions', default=5)
    parser.add_argument('--force', action='store_true', help='Overwrite existing json output', default=True)
    parser.add_argument('--output', type=str, help='Path to output directory', default='./output/')
    args = parser.parse_args()

    model = args.model 
    dialect = args.dialect
    force = args.force
    num_subtopics = args.num_subtopics
    num_questions = args.num_questions
    output = args.output
    
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
    
    output_dir = os.path.join(output, f'{dialect}_dataset')
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f'{dialect}_dataset.json')
    if force and os.path.exists(json_path):
        os.remove(json_path)
        
    logger = get_logger(os.path.join(output, f'{dialect}_generate.log'))

    query_generator = QueryGenerator(
        config=config,
        model_name=model,
        dialect=dialect,
        logger=logger
    )
    
    for view in [View.Liberty]:
        view_tables = get_table_names(
            source=view.value
        ) 

        query_generator.generate(
            view=view.value,
            schema=config.db_config.pdk_database.get_table_info(view_tables),
            table_descr=get_desc(view.value),
            num_subtopics=num_subtopics,
            num_questions=num_questions,
            subtopics=SUBTOPICS_BYVIEW[view.value],
            json_path=json_path
        )

        stats = count_stats(json_path)
        logger.info(f"BLUE: Generated SQL Stats \n {stats}")
        
        
if __name__ == '__main__':
    main()