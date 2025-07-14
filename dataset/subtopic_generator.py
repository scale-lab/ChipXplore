"""
Subtopic Generator
"""

import os 
import json
import argparse
from dataset.model import GPTModel

from config.sky130 import View
from core.utils import get_logger
from dataset.dataset_utils import parse_json_list_from_string
from core.database.sql import get_desc, get_table_names
from dataset.subtopics.subtopics import SUBTOPICS_BYVIEW
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig


SYS_PROMPT = """You are a senior and expert hardware engineer who can come up with relevant topics according to the provided instructions."""

USER_INSTRUCTION = lambda dialect, schema, table_descr, num_subqtopics:  f"""
Following is a schema of a {dialect} database.
{schema}

Following is the table description of the given schema. 
{table_descr}

Instruction:
    [1] Provide {num_subqtopics} key sub-topics or areas from which important questions can be asked by a hardware engineer based on the information provided in the schema and table description.
    [2] Provide the sub-topics in the following JSON format: 
```json
    {{
        "id": "<sub-topic-id>",
        "name": "<sub-topic-name>",
        "description": "<sub-topic-description>"
    }}
```   
"""


class SubTopicGenerator:

    def __init__(self, model_name) -> None:
        self.system_prompt = SYS_PROMPT
        self.model = GPTModel(
            name=model_name
        )

    def generate(self, dialect, schema, table_descr, num_subtopics): 
        
        self.user_instructions = USER_INSTRUCTION(
            dialect=dialect,
            schema=schema,
            table_descr=table_descr,
            num_subqtopics=num_subtopics,
        )

        response = self.model.message(
            system_prompt=self.system_prompt, 
            user_prompt=self.user_instructions,
            temperature=0
        ) 

        subtopics = parse_json_list_from_string(response[0])
        return subtopics 
    
 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--dialect', type=str, help='Query dialect', default='SQL')
    parser.add_argument('--num_subtopics', type=int, help='Number of questions', default=5)
    parser.add_argument('--output', type=str, help='Path to output directory', default='./output/')
    args = parser.parse_args() 

    dialect = args.dialect 
    num_subtopics = args.num_subtopics
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

    logger = get_logger(os.path.join(output, 'subtopic_generator.log'))

    topic_generator = SubTopicGenerator(
        model_name=model
    ) 

    for view in View:
        view_tables = get_table_names(
            source=view.value
        ) 
        subtopics = topic_generator.generate(
            dialect=dialect,
            schema=config.db_config.pdk_database.get_table_info(view_tables),
            table_descr=get_desc(view.value),
            num_subtopics=num_subtopics
        )

        for subtopic in subtopics:
            logger.info(f"BLUE: Generated Subtopic Name, {subtopic['name']}")
            logger.info(f"YELLOW: Generated Subtopic Description, {subtopic['description']}")



if __name__ == '__main__':
    main()
