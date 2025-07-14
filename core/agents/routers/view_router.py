import re
import os
import json 
from enum import Enum
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
)
from typing import List


import argparse

from dotenv import load_dotenv
load_dotenv()

from config.sky130 import View
from core.agents.agent import Agent
from core.agents.routers.const import lef_template, lib_template, tlef_template
from core.agents.few_shot.view import view_router_few_shot
from core.eval.test_set import test_queries, test_queries_tlef, test_queries_lib, test_queries_lef
from core.agents.utils import parse_json_from_string
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.utils import get_logger
from core.graph_flow.states import PDKQueryState



class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    explain: str = Field( 
        description="Reasoning for choosing the view"
    )
    view: Literal["Liberty",  "Lef" , "TechnologyLef"] = Field(
        description="Given a user question choose which datasource would be most relevant for answering their question",
    )


json_format = """{{
  "explain": "<explanation-of-your-choice>",
  "view": "<routed-view>"  
}}
"""

VIEW_ROUTER_SYS_PROMPT = f'''You are an expert at routing user questions to the appropriate view in the Process Design Kit (PDK).
The PDK has the following three distinct views:  

[1] {View.Liberty.value} view: 
- Contains the following charactersics of cells:
  * Cell timing information (delay, gate capacitance, etc.)
  * Input pin capacitances
  * Overall cell area (as a single value, not dimensions)
  * Input and output pin timing information (transition time, propagation delay, internal power)
- DOES NOT contain physical dimensions (width, height) or layout information
Here is an example of the information present in the Liberty view: 
{lib_template}
      
[2] {View.Lef.value} view: 
- Contains physical layout information of cells, including:
  * Exact width and height of each cell
  * Pin physical information (layers, pin rectangles and their coordinates)
  * Pins antenna gate area
  * Antenna ratios for input and output pins
  * Power and ground pin names in the layout
  * Cell obstruction shapes and their layers
- DOES NOT contain electrical characteristics or timing information
Here is an example of the information present in the Lef view: 
{lef_template}

[3] {View.TechLef.value} view: 
- Contains process-specific design rules and technology information, including:
  * Metal (routing) and via (cut) layer rules (minimum width, pitch, thickness, offset)
  * Available routing and cut layers in the PDK and their antenna area ratios
  * Metal layer properties (pitch, width, spacing, offset)
  * Via layer (cut layer) specifications
- DOES NOT contain cell-specific information or layout details
Here is an example of the information present in the TechnologyLef view: 
{tlef_template}
                         
Give an explanation first for why you are choosing a specific view then output the JSON format.
'''

FEW_SHOT_TEMPLATE = """User question: {input}
Data source:
{route_query}
"""

class ViewRouter(Agent):
    """
        Routes user questions to the appropriate view in the library
    """
    def __init__(self, config) -> None:
        super().__init__(context_winow=5048, output_tokens=512)
        self.config = config 
       
        system = VIEW_ROUTER_SYS_PROMPT 
        if config.flow_config.few_shot: 
            system += "Here are some examples for user questions and their corresponding relevant view:"
            self.prompt = FewShotPromptTemplate(
                examples=view_router_few_shot,
                example_prompt=PromptTemplate.from_template(
                    FEW_SHOT_TEMPLATE
                ),
                input_variables=["input", "route_query"],
                prefix=system,
                suffix="Give the view for the following user question. \nUser question: {input}",
            )
        else:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", str(system)),
                    ("user", "{input}"),
                ]
            )

        self.llm = config.lm_config.router_llm_model
        # structured_llm = self.llm.with_structured_output(
        #     RouteQuery, 
        #     include_raw=True
        # )
            
        self.router = self.prompt | self.llm
        
    def route(self, state: PDKQueryState):
        if self.config.flow_config.use_router: 
            query = state.get("question")
            if "deepseek-chat" in self.config.lm_config.router_lm_name: ## Hacky fix to unreliable API
                received = False
                while not received: 
                    try: 
                        stream = self.router.stream({"input": query})
                        full = next(stream)
                        for chunk in stream:
                            full += chunk
                        full
                        received = True 
                    except ValueError as e:
                        print(f"[Reasoner]: Exception Happened Retrying... {e}")
                out = full
            else: 
                out = self.router.invoke({"input": query})
           
            content_json = parse_json_from_string(out.content)
            response = RouteQuery(**content_json)
            # if out['parsed'] is None: 
            #     content = out['raw'].content
            #     content_json = parse_json_from_string(content)
            #     out['parsed']  = RouteQuery(**content_json)
           
            # response = out['parsed'] 
            return {"view": response.view}
        else:
            return {"view": ""}
        

    def view_metric(self, gold, pred):
        if pred is None:
            return 0 
        return set(gold) == set(pred) 


__all__ = [
  'ViewRouter',
]



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/router_eval.log')
    args = parser.parse_args()
    
    model = args.model 
    output = args.output 
    few_shot = not args.wo_fewshot

    logger = get_logger(output)
    
    logger.info(f"YELLOW: \n LLM Agent {model}") 
    logger.info(f"CYAN: Few Shot Set to {few_shot}") 

    # Router agent
    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=True,
            use_planner=True,
            use_router=False,
            use_selector=True,
            decompose_query=True,
            use_refiner=True,
            use_in_mem_db=True,
            graph_recursion_limit=10
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
            partition=True,
            in_mem_db=True
        ),
    )
    
    view_router = ViewRouter(
       config=config
    )
   
    view_prompt = view_router.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?"
    )
    logger.info(f"MAGENTA: \n View Router Prompt \n {view_prompt}") 

    view_correct = 0
    for query in test_queries: 
        logger.info(f"CYAN: {query['input']}")

        routed_view= view_router.route(
            {"question": query["input"]}
        )
       
        view_score = view_router.view_metric(
            gold=query['view'],
            pred=routed_view['view']
        )
        view_correct += view_score
        
        color = "GREEN" if  view_score else "RED"
        logger.info(f"{color}: \n Routed View: {routed_view}")
        # logger.info(f"{color}: \n Explaination: {routed_view.explain}")

        break 
      
    router_accuracy = view_correct / len(test_queries)
    logger.info(f"BLUE: \n View Router accuracy is {router_accuracy}")


if __name__ == '__main__':
    main()