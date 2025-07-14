"""Table Selector
    Selects relevant table for a given user query. 
"""
import os
import re
import json
import logging
import argparse


from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.example_selectors.base import BaseExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


from config.sky130 import cell_variant_sky130, get_corner_name, View
from core.agents.few_shot.selector import selector_few_shot
from core.agents.few_shot.selector_partitioned import selector_few_shot_partition
from core.agents.utils import parse_json_from_string
from core.eval.test_set import test_queries, test_queries_lef, test_queries_tlef, test_queries_lib
from core.database.sql import get_desc, get_fk, get_table_names
from core.agents.routers.router import  Router
from core.agents.agent import Agent
from core.graph_flow.states import PDKQueryState
from core.utils import get_logger


# Define your desired data structure.
class SelectedLibSchema(BaseModel):
    Operating_Conditions: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Operating_Conditions' table, providing data on various operating conditions like temperature and voltage levels.This is needed most to filter entries in the Cells table associated with the operating conditions the question is referring to."
    )
    Cells: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Cells' table, which contains detailed information about the individual cells or components within a library."
    )
    Input_Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Input_Pins' table, listing all input pins available in the library's cells."
    )
    Output_Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Output_Pins' table,, which lists all output pins of the cells in the library."
    )
    Timing_Values: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Timing_Values', which includes the timing values table associated with each output pin."
    )
    
    def get_selected_columns(self):
        columns = []
        if self.Operating_Conditions.lower() == 'keep':
            columns.append('Operating_Conditions')
            
        if self.Cells.lower() == 'keep':
            columns.append('Cells')
        
        if self.Input_Pins.lower() == 'keep':
            columns.append('Input_Pins')
        
        if self.Output_Pins.lower() == 'keep':
            columns.append('Output_Pins')
        
        if self.Timing_Values.lower() == 'keep':
            columns.append('Timing_Values')
                
        
        return columns


        
class SelectedLefSchema(BaseModel):
    Macros: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Macros' table, which includes definitions of various cells (i.e macros)."
    )
    
    Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Pins' table, detailing the pins of the macros (cells)."
    )
    
    Pin_Ports: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'PinPorts' table, listing physical ports of each pin."
    )
    
    Pin_Port_Rectangles: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'PinPortRectangles' table, which provides geometric descriptions of each pin port in rectangular shapes."
    )
    
    Obstructions: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Obstructions' table, which provides the obstruction layers within each macro/cell layout ."
    )
    
    Obstruction_Rectangles: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'ObstructionRectangles' table, detailing the geometric shapes of obstructions in the macro/cell layout."
    )
    
    def get_selected_columns(self):
        columns = []
        if self.Macros.lower() == 'keep':
            columns.append('Macros')
        
        if self.Pins.lower() == 'keep':
            columns.append('Pins')
        
        if self.Pin_Ports.lower() == 'keep':
            columns.append('Pin_Ports')
            
        if self.Pin_Port_Rectangles.lower() == 'keep':
            columns.append('Pin_Port_Rectangles')
            
        if self.Obstructions.lower() == 'keep':
            columns.append('Obstructions')

        if self.Obstruction_Rectangles.lower() == 'keep':
            columns.append('Obstruction_Rectangles')
          
        return columns 
    


class SelectedTechLefSchema(BaseModel):
    Routing_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Routing_Layers' table, which contains information about the layers used for routing signals."
    )
    
    Cut_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Cut_Layers' table, which contains information about the via cut layers."
    )
    
    Antenna_Diff_Side_Area_Ratios: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Antenna_Diff_Side_Area_Ratios' table, which includes antenna ratios for the routing layers."
    )
    
    Antenna_Diff_Area_Ratios: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Antenna_Diff_Area_Ratios' table,  which includes antenna ratios for the cut layers.."
    )
    
    Vias: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the'Vias' table, which includes details about the types and configurations of vias ."
    )
    
    Via_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Via_Layers' table, detailing information about the via layers."
    )
    
    def get_selected_columns(self):
        columns = []
        if self.Routing_Layers.lower() == 'keep':
            columns.append('Routing_Layers')
        
        if self.Cut_Layers.lower() == 'keep':
            columns.append('Cut_Layers')
        
        if self.Antenna_Diff_Side_Area_Ratios.lower() == 'keep':
            columns.append('Antenna_Diff_Side_Area_Ratios')
            
        if self.Antenna_Diff_Area_Ratios.lower() == 'keep':
            columns.append('Antenna_Diff_Area_Ratios')
            
        if self.Vias.lower() == 'keep':
            columns.append('Vias')

        if self.Via_Layers.lower() == 'keep':
            columns.append('Via_Layers')
            
        return columns 


class SelectedSchema(BaseModel):
    Routing_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Routing_Layers' table, which contains information about the layers used for routing signals."
    )
    
    Cut_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Cut_Layers' table, which contains information about the via cut layers."
    )
    
    Antenna_Diff_Side_Area_Ratios: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Antenna_Diff_Side_Area_Ratios' table, which includes antenna ratios for the routing layers."
    )
    
    Antenna_Diff_Area_Ratios: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Antenna_Diff_Area_Ratios' table,  which includes antenna ratios for the cut layers.."
    )
    
    Vias: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the'Vias' table, which includes details about the types and configurations of vias ."
    )
    
    Via_Layers: str = Field(
        default='keep',
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Via_Layers' table, detailing information about the via layers."
    )
    
    Macros: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Macros' table, which includes definitions of various cells (i.e macros)."
    )
    
    Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Pins' table, detailing the pins of the macros (cells)."
    )
    
    Pin_Ports: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'PinPorts' table, listing physical ports of each pin."
    )
    
    Pin_Port_Rectangles: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'PinPortRectangles' table, which provides geometric descriptions of each pin port in rectangular shapes."
    )
    
    Obstructions: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Obstructions' table, which provides the obstruction layers within each macro/cell layout ."
    )
    
    Obstruction_Rectangles: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'ObstructionRectangles' table, detailing the geometric shapes of obstructions in the macro/cell layout."
    )

    Operating_Conditions: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Operating_Conditions' table, providing data on various operating conditions like temperature and voltage levels.This is needed most to filter entries in the Cells table associated with the operating conditions the question is referring to."
    )
    Cells: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Cells' table, which contains detailed information about the individual cells or components within a library."
    )
    Input_Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Input_Pins' table, listing all input pins available in the library's cells."
    )
    Output_Pins: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Output_Pins' table,, which lists all output pins of the cells in the library."
    )
    Timing_Values: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Timing_Values', which includes the timing values table associated with each output pin."
    )

    def get_selected_columns(self):
        columns = []
        if self.Routing_Layers.lower() == 'keep':
            columns.append('Routing_Layers')
        
        if self.Cut_Layers.lower() == 'keep':
            columns.append('Cut_Layers')
        
        if self.Antenna_Diff_Side_Area_Ratios.lower() == 'keep':
            columns.append('Antenna_Diff_Side_Area_Ratios')
            
        if self.Antenna_Diff_Area_Ratios.lower() == 'keep':
            columns.append('Antenna_Diff_Area_Ratios')
            
        if self.Vias.lower() == 'keep':
            columns.append('Vias')

        if self.Via_Layers.lower() == 'keep':
            columns.append('Via_Layers')
        
        if self.Macros.lower() == 'keep':
            columns.append('Macros')
        
        if self.Pins.lower() == 'keep':
            columns.append('Pins')
        
        if self.Pin_Ports.lower() == 'keep':
            columns.append('Pin_Ports')
            
        if self.Pin_Port_Rectangles.lower() == 'keep':
            columns.append('Pin_Port_Rectangles')
            
        if self.Obstructions.lower() == 'keep':
            columns.append('Obstructions')

        if self.Obstruction_Rectangles.lower() == 'keep':
            columns.append('Obstruction_Rectangles')

        if self.Operating_Conditions.lower() == 'keep':
            columns.append('Operating_Conditions')
            
        if self.Cells.lower() == 'keep':
            columns.append('Cells')
        
        if self.Input_Pins.lower() == 'keep':
            columns.append('Input_Pins')
        
        if self.Output_Pins.lower() == 'keep':
            columns.append('Output_Pins')
        
        if self.Timing_Values.lower() == 'keep':
            columns.append('Timing_Values')
                
        return columns 
    

class CustomExampleSelector(BaseExampleSelector):
    """Few shot selector based on the routed library vew
    """
    def __init__(self, examples):
        self.examples = examples

    def add_example(self, example):
        self.examples.append(example)

    def select_examples(self, input_variables):
        input_view = input_variables["view"]
        best_match = []
        for example in self.examples:
            if example['source'] == input_view:
                best_match.append(example)

        return best_match

def get_out_format(view=None, partition=False):
    if view == 'Liberty':

        if partition: 
            return """
```json
"Cells": "<keep-or-drop>",  
"Input_Pins": "<keep-or-drop>",  
"Output_Pins": "<keep-or-drop>",
"Timing_Values": "<keep-or-drop>",
```
""" 
        else:

            return """
```json
"Operating_Conditions": "<keep-or-drop>",  
"Cells": "<keep-or-drop>",  
"Input_Pins": "<keep-or-drop>",  
"Output_Pins": "<keep-or-drop>",
"Timing_Values": "<keep-or-drop>",
```
""" 
        
    if view == 'Lef': 
        return """
```json
"Macros": "<keep-or-drop>",  
"Pins": "<keep-or-drop>",  
"Pin_Ports": "<keep-or-drop>",  
"Pin_Port_Rectangles": "<keep-or-drop>",  
"Obstructions": "<keep-or-drop>",  
"Obstruction_Rectangles": "<keep-or-drop>"
```
"""

    if view == 'TechnologyLef': 
        return """
```json
"Routing_Layers": "<keep-or-drop>",  
"Antenna_Diff_Side_Area_Ratios": "<keep-or-drop>",  
"Cut_Layers": "<keep-or-drop>",  
"Antenna_Diff_Area_Ratios": "<keep-or-drop>",  
"Vias": "<keep-or-drop>",  
"Via_Layers": "<keep-or-drop>"
```     
""" 

    if view is None or view == "": 
        if partition:
            return """
```json
"Cells": "<keep-or-drop>",  
"Input_Pins": "<keep-or-drop>",  
"Output_Pins": "<keep-or-drop>",
"Timing_Values": "<keep-or-drop>",
"Macros": "<keep-or-drop>",  
"Pins": "<keep-or-drop>",  
"Pin_Ports": "<keep-or-drop>",  
"Pin_Port_Rectangles": "<keep-or-drop>",  
"Obstructions": "<keep-or-drop>",  
"Obstruction_Rectangles": "<keep-or-drop>",
"Routing_Layers": "<keep-or-drop>",  
"Antenna_Diff_Side_Area_Ratios": "<keep-or-drop>",  
"Cut_Layers": "<keep-or-drop>",  
"Antenna_Diff_Area_Ratios": "<keep-or-drop>",  
"Vias": "<keep-or-drop>",  
"Via_Layers": "<keep-or-drop>"
```
""" 
        else: 
            return """
```json
"Operating_Conditions": "<keep-or-drop>",  
"Cells": "<keep-or-drop>",  
"Input_Pins": "<keep-or-drop>",  
"Output_Pins": "<keep-or-drop>",
"Timing_Values": "<keep-or-drop>",
"Macros": "<keep-or-drop>",  
"Pins": "<keep-or-drop>",  
"Pin_Ports": "<keep-or-drop>",  
"Pin_Port_Rectangles": "<keep-or-drop>",  
"Obstructions": "<keep-or-drop>",  
"Obstruction_Rectangles": "<keep-or-drop>",
"Routing_Layers": "<keep-or-drop>",  
"Antenna_Diff_Side_Area_Ratios": "<keep-or-drop>",  
"Cut_Layers": "<keep-or-drop>",  
"Antenna_Diff_Area_Ratios": "<keep-or-drop>",  
"Vias": "<keep-or-drop>",  
"Via_Layers": "<keep-or-drop>"
```
"""
    
    
SELECTOR_SYS_PROMPT = """As an experienced and professional database administrator, your task is to analyze a user question
and a database schema to provide relevant information. The database schema consists of table
descriptions, each containing multiple column descriptions. Your goal is to identify the relevant
tables based on the user question.

[Instruction]
1. Discard any table schema that is not related to the user question. 
2. The output must be in JSON format: 
{output_format}

3. You must mark all tables in your JSON output. 

[Requirements]
1. If a table is relevant to the user question, mark it as "keep". 
2. If a table is completely irrelevant to the user question, mark it as "drop". 
3. If you are unsure about the table relevance, still mark it as "keep". 
4. If you need data from Table A and Table C, and Table B connects them using the foreign key, you must include Table B in your selection.

Below is the schema description for the tables. Use the foreign keys to determine connection between tables: 
Tables: 
{desc_str}

Foreign Keys: 
{fk_str}
""" 


def parse_table_selection(json_string):
    cleaned_json = json_string.strip().strip('`').strip()
    if cleaned_json.startswith('json'):
        cleaned_json = cleaned_json[4:].strip()
    
    table_dict = json.loads(cleaned_json)
    
    return {k: v.lower() == 'keep' for k, v in table_dict.items()}





SELECTOR_FEW_SHOT_TEMPLATE="""
Think step by step about the needed tables, then output your answer in json format: 

User input: {input} 

Reasoning Step-by-step: 
{selection_steps}

Selected tables: {tables}
"""

SELECTOR_SUFFIX = """Think step by step about the needed tables, then output your answer in json format. Give your answer in the same format as the given examples: 

User input {input} 
"""

class SchemaSelector(Agent):
    """Dynamically selects the tables relevant to the user query. 
    """
    def __init__(self, config, custom_selector=True) -> None:
        super().__init__(context_winow=5028, output_tokens=1048)
        self.config = config
        system = SELECTOR_SYS_PROMPT

        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding relevant tables:"

            if config.db_config.partition: 
                example_selector = CustomExampleSelector(selector_few_shot_partition)
            elif custom_selector: 
                example_selector = CustomExampleSelector(selector_few_shot)
            else: 
                example_selector =  SemanticSimilarityExampleSelector.from_examples(
                    selector_few_shot,  
                    OpenAIEmbeddings(),
                    FAISS,
                    k=2,           
                )

            self.prompt = FewShotPromptTemplate(
                example_selector=example_selector,
                example_prompt=PromptTemplate.from_template(SELECTOR_FEW_SHOT_TEMPLATE),
                input_variables=['input', 'view', 'desc_str', 'fk_str', 'tables', 'question'],
                prefix=system,
                suffix=SELECTOR_SUFFIX,
            )
        
        else: 
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system),
                    ("human", "{input}"),
                ]
            )

        self.llm = config.lm_config.selector_llm_model
        
        self.selector = self.prompt | self.llm

    def select(self, state: PDKQueryState):

        if self.config.flow_config.use_selector: 
            view = state.get("view", "")
            query = state.get("question")
            scl_library = state.get("scl_library", [])
            voltage_corner = state.get("voltage_corner")
            temp_corner = state.get("temp_corner")
            techlef_corner = state.get("techlef_op_cond")
            
            desc_str = get_desc(
                source=view, 
                partition=self.config.db_config.partition
            )
            fk_str = get_fk(
                source=view, 
                partition=self.config.db_config.partition
            )
            view_table_names = get_table_names(
                source=view, 
                partition=self.config.db_config.partition
            )

            pvt_corner = None
            if view == View.Liberty.value: 
                pvt_corner = get_corner_name(
                    scl_library=cell_variant_sky130(scl_library), 
                    voltage=voltage_corner, 
                    temperature=temp_corner
                )
           
            database = self.config.db_config.get_database(
                view=view,
                scl_library=cell_variant_sky130(scl_library),
                pvt_corner=pvt_corner,
                techlef_corner=techlef_corner
            )

            table_info = database.get_table_info(table_names=view_table_names)
            
            output_format = get_out_format(view, partition=self.config.db_config.partition) 

            if "deepseek-chat" in self.config.lm_config.selector_lm_name: ## Hacky fix to unreliable API
                received = False
                while not received: 
                    try: 
                        stream = self.selector.stream({
                            'input': query, 
                            'view': view, 
                            'desc_str': desc_str, 
                            'output_format': output_format,
                            'fk_str': fk_str, 
                            'table_info': table_info
                        })
                        full = next(stream)
                        for chunk in stream:
                            full += chunk
                        full
                        received = True 
                    except ValueError as e:
                        print(f"[Reasoner]: Exception Happened Retrying... {e}")
                output = full 
            else: 
                output = self.selector.invoke({
                    'input': query, 
                    'view': view, 
                    'desc_str': desc_str, 
                    'output_format': output_format,
                    'fk_str': fk_str, 
                    'table_info': table_info
                })

            if type(output) != str: 
                output = output.content

            selected_tables = parse_json_from_string(output)

            if view == 'Liberty':
                output = SelectedLibSchema(**selected_tables)
                if self.config.db_config.partition: 
                    output.Operating_Conditions = 'drop'
            elif view == 'Lef':
                output = SelectedLefSchema(**selected_tables)
            elif view == 'TechnologyLef':
                output = SelectedTechLefSchema(**selected_tables)
            elif view is None or view == "":
                if selected_tables is None:
                    output = SelectedSchema() 
                else: 
                    output = SelectedSchema(**selected_tables)

            selected_schema = output.get_selected_columns()
            print(selected_schema)
            desc_str = get_desc(
                source=view, 
                selected_schema=selected_schema,  
                partition=self.config.db_config.partition
            )
            fk_str = get_fk(
                source=view, 
                selected_schema=selected_schema,
                partition=self.config.db_config.partition
            )
            table_info =  database.get_table_info(table_names=selected_schema)

            return {'tables': selected_schema, 'desc_str': desc_str, 'fk_str': fk_str, 'table_info': table_info, 'pvt_corner': pvt_corner}
        else: 
            view = state.get("view", "")
            scl_library = state.get("scl_library", [])
            voltage_corner = state.get("voltage_corner")
            temp_corner = state.get("temp_corner")
            techlef_corner = state.get("techlef_op_cond")

            pvt_corner = None
            if view == View.Liberty.value: 
                pvt_corner = get_corner_name(
                    scl_library=cell_variant_sky130(scl_library), 
                    voltage=voltage_corner, 
                    temperature=temp_corner
                )
           
            database = self.config.db_config.get_database(
                view=view,
                scl_library=cell_variant_sky130(scl_library),
                pvt_corner=pvt_corner,
                techlef_corner=techlef_corner
            )

            partition = self.config.db_config.partition
            tables = get_table_names(source=None, partition=partition)
            desc_str = get_desc(source=None, selected_schema=None,  partition=partition)
            fk_str = get_fk(source=None, partition=partition)
            table_info = database.get_table_info(table_names=tables)

            return {'tables': tables, 'desc_str': desc_str, 'fk_str': fk_str, 'table_info': table_info} 
        

    def compute_exact_accuracy(self, pred_tables, ground_truth):
        is_exact = set(ground_truth)==(set(pred_tables))           
        return is_exact 

    def compute_subset_accuracy(self, pred_tables, ground_truth):
        is_subset = set(ground_truth).issubset(set(pred_tables))     
        return is_subset 


__all__ = [
  'SchemaSelector'
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_router', action='store_true', default=False)
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/selector_eval.log')
    args = parser.parse_args()

    output = args.output
    model = args.model 
    use_router = not args.wo_router
    few_shot = not args.wo_fewshot
    
    logger = get_logger(output)

    logger.info(f"CYAN: LLM Agent is {model}") 
    logger.info(f"CYAN: Few Shot Set to {few_shot}") 

    database = SQLDatabase.from_uri("sqlite:///dbs/sky130.db")

    # Init LLM agents
    router = Router(
        model=model,
        temperature=0,
        few_shot=True
    ) 
    selector = SchemaSelector(
        few_shot=few_shot,
        model=model,
        temperature=0
    )
    
    view_prompt = router.view_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")
    scl_prompt = router.scl_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")
    selector_prompt = selector.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?", 
        view='Liberty', 
        desc_str=get_desc('Liberty'), 
        fk_str=get_fk('Liberty'), 
        output_format=get_out_format('Liberty'),
        table_info=database.get_table_info(table_names=get_table_names('Liberty'))
    )

    logger.info(f"MAGENTA: View Router Prompt is {view_prompt}") 
    logger.info(f"MAGENTA: SCL Router Prompt is {scl_prompt}") 
    logger.info(f"MAGENTA: Selector Prompt for liberty is {selector_prompt}") 

    view_correct = 0
    scl_corect = 0
    selector_exact_correct = 0 
    selector_relaxed_correct = 0
    
    for query in test_queries:

        logger.info(f"CYAN: {query['input']}")        
     
        if use_router: 
            routed_scl_variant, routed_view, routed_op_cond = router.route(
                query=query["input"]
            )                
            view = routed_view.datasource
            scl_varaint = routed_scl_variant 
        else:
            view = None
            scl_varaint = None

        # filter tables based on the routed view
        desc_str = get_desc(view, compact=False)
        fk_str = get_fk(view)
        view_table_names = get_table_names(view)
        table_info = database.get_table_info(table_names=view_table_names)
        
        # logger.info(f"YELLOW: table descriptions {desc_str}")
        # logger.info(f"YELLOW: Table Info {table_info}")
        logger.info(f"YELLOW: Foreign Key {fk_str}")

        color = 'GREEN' if view == query["view"] else 'RED'
        logger.info(f"{color}: Routed View: {view}")
        
        color = 'GREEN' if scl_varaint == query["scl_variant"] else 'RED'
        logger.info(f"{color}: SCL Variant: {scl_varaint}")
        
        # selectror only looks at the view table info 
        selected_tables = selector.select(
            query=query['input'], 
            datasource=view, 
            desc_str=desc_str, 
            fk_str=fk_str, 
            table_info=table_info, 
        )
        
        exact_score = selector.compute_exact_accuracy(
            selected_tables.get_selected_columns(), 
            query["selected_tables"]
        )
        relaxed_score = selector.compute_subset_accuracy(
            selected_tables.get_selected_columns(), 
            query["selected_tables"]
        )

        tables = selected_tables.get_selected_columns()
        color = 'GREEN' if relaxed_score else 'RED'
        logger.info(f"{color}: Selected Tables are {tables}")

        view_correct = view_correct + 1 if view == query["view"] else view_correct
        scl_corect = scl_corect + 1 if scl_varaint == query["scl_variant"] else scl_corect
        selector_exact_correct += 1 if exact_score else 0 
        selector_relaxed_correct += 1 if relaxed_score else 0

    view_router_accuracy = view_correct / len(test_queries)
    scl_router_accuracy = scl_corect / len(test_queries)
   
    selector_exact_accuracy = selector_exact_correct / len(test_queries)
    selector_relaxed_accuracy = selector_relaxed_correct / len(test_queries)

    logger.info(f"BLUE: View Router Accuracy is {view_router_accuracy}")
    logger.info(f"BLUE: SCL Router Accuracy is {scl_router_accuracy}")
    logger.info(f"BLUE: Selector Exact Accuracy is {selector_exact_accuracy}")
    logger.info(f"BLUE: Selector Subset Accuracy is {selector_relaxed_accuracy}")


if __name__ == '__main__':
    main()