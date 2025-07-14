
"""
Question Generator
"""
import os 
import json
import argparse
from dataset.model import GPTModel

from config.sky130 import View
from core.utils import get_logger
from core.database.sql import get_desc, get_table_names
from dataset.subtopics.subtopics import SUBTOPICS_BYVIEW
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from dataset.dataset_utils import parse_json_list_from_string


SYS_PROMPT = f"""You are an expert hardware engineer. Accordingly follow the given instructions."""

USER_INSTRUCTION = lambda dialect, schema, table_descr, num_questions, subtopic: f"""\

Following is a {dialect} database schema:
{schema}

Following is the table description of the given schema. 
{table_descr}

[Requirements]
    [1] The questions must be answerable using {dialect} queries from the information present in the table whose schema is given.
    [2] Don't generate questions that would require returing all entries in the database.
    [3] Don't generate questions that would require returning all columns in a table. 
    [4] Make your questions concise.
    [5] Provide the output in JSON format with the following: 
``json
{{
    "1": "<first-question>",
    "2": "<second-question>",
    ....
}}
```

Generate {num_questions} questions for the following sub-topic following [requirements]: 

{subtopic['name']}: {subtopic['description']}
"""


class QuestionGenerator:

    def __init__(self, model_name) -> None:
        self.system_prompt = SYS_PROMPT
        self.model = GPTModel(
            name=model_name
        )

    def generate(self, dialect, schema, table_descr, subtopic, num_questions): 
        self.user_instructions = USER_INSTRUCTION(
            dialect=dialect,
            schema=schema,
            table_descr=table_descr,
            num_questions=num_questions,
            subtopic=subtopic
        )

        response = self.model.message(
            system_prompt=self.system_prompt, 
            user_prompt=self.user_instructions,
            temperature=0
        ) 

        questions = parse_json_list_from_string(response[0])[0]

        return questions 
    
 



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--dialect', type=str, help='Query dialect', default='SQL')
    parser.add_argument('--num_questions', type=int, help='Number of questions', default=3)
    parser.add_argument('--output', type=str, help='Path to output directory', default='./output/')
    args = parser.parse_args()

    dialect = args.dialect 
    num_questions = args.num_questions
    output = args.output 
    model = args.model    

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
    
    logger = get_logger(os.path.join(output, 'question_generator.log'))

    question_generator = QuestionGenerator(
        model_name=model
    ) 

    for view in View:
        view_tables = get_table_names(
            source=view.value
        ) 
        
        for subtopic in SUBTOPICS_BYVIEW[view.value]: 
            logger.info(f"YELLOW: Subtopic, {subtopic['name']}")
            logger.info(f"CYAN: Subtopic Description, {subtopic['description']}")
            questions = question_generator.generate(
                dialect=dialect, 
                schema=config.db_config.pdk_database.get_table_info(view_tables), 
                table_descr=get_desc(view.value), 
                subtopic=subtopic, 
                num_questions=num_questions
            )

            for _, q in questions.items(): 
                logger.info(f"BLUE: Questions, {q}")


            break 

if __name__ == '__main__':
    main()