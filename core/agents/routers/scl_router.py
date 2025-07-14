from typing import Literal
from typing_extensions import TypedDict

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


import os
import argparse

from core.agents.agent import Agent
from core.agents.utils import parse_json_from_string
from core.agents.few_shot.scl import  scl_router_few_shot
from core.eval.test_set import test_queries, test_queries_lef, test_queries_tlef, test_queries_lib
from core.graph_flow.states import PDKQueryState
from core.utils import get_logger
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig

from dotenv import load_dotenv
load_dotenv()



SCL_ROUTER_SYS_PROMPT= f"""You are an expert at routing a user questions to the appropriate standard cell variant in the Process Design Kit (PDK).
        
[Instruction]
1. Discard any stanadard cell library that is not related to the user question. 
2. The output should be in JSON format. 

[Requirements]
1. If a standard cell library is relevant to the user question, mark it as "keep". 
2. If a standard cell library is completely irrelevant to the user question, mark it as "drop". 

The PDK has the following standard cell variants:

    [1] HighDensity: High Density (HD) Digital Standard Cells :
       HighDensity Prefix is sky130_fd_sc_hd
    
    [2] HighDensityLowLeakage: High Density Low Leakage (HDLL) Digital Standard Cell: 
        HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
    
    [3] HighSpeed: High Speed (HS) Digital Standard Cells: 
        HighSpeed Prefix is sky130_fd_sc_hs

    [4] LowSpeed: Low Speed (LS) Digital Standard Cells: 
        LowSpeed Prefix is sky130_fd_sc_ls

    [5] MediumSpeed: Medium Speed (MS) Digital Standard Cells
        MediumSpeed Prefix is sky130_fd_sc_ms

    [6] LowPower: Low Power (LP) Digital Standard Cells
        LowPower Prefix is sky130_fd_sc_lp

Based on the information the question is referring to, route it to the relevant standard cell library variant. 

Pay attention to the cell name in the question:

    - sky130_fd_sc_hd: Route to HighDensity 
    - sky130_fd_sc_hdll: Route to HighDensityLowLeakage 
    - sky130_fd_sc_hs: Route to HighSpeed 
    - sky130_fd_sc_ls: Route to LowSpeed 
    - sky130_fd_sc_ms: Route to MediumSpeed 
    - sky130_fd_sc_lp: Route to LowPower 
    
User could specify library name in lower case: 
    - high density: Route to HighDensity 
    - high density low leakage: Route to HighDensityLowLeakage 
    - high speed: Route to HighSpeed 
    - low speed: Route to LowSpeed 
    - medium speed: Route to MediumSpeed 
    - low power: Route to LowPower 

User could specify multiple libraries in the question: 
    - high density and low speed: Route to HighDensity and LowSpeed
    - high speed and medium speed: Route to HighSpeed and MediumSpeed
    - low speed and low power: Route to LowSpeed and LowPower

If a question requires comparing all libraries, mark all libraries as keep. 

If you can't infer the standard cell library from the user question, choose the default library which is HighDensity. 

Give an explanation first for why you are choosing a specific library then output the JSON format
"""


class StandardCellLibrary(BaseModel):
    """Route a user query to the most relevant datasource."""
    Explain: str = Field(description="Explanaiton for the library choice", default='')
    HighDensity: str = Field(description="Use high density standard cell library", default='keep')
    HighDensityLowLeakage: str = Field(description="Use high density standard cell library", default='drop')
    HighSpeed: str = Field(description="Use High Speed standard cell library.",default='drop')
    LowSpeed: str = Field(description="Use Low Speed standard cell library.",default='drop')
    MediumSpeed: str = Field(description="Use Medium Speed Library.0", default='drop')
    LowPower: str = Field(description="Use Medium Speed Library.", default='drop')

    def get_libraries(self): 
        libraries = []
        if self.HighDensity.lower() == 'keep':
            libraries.append('HighDensity') 
        
        if self.HighDensityLowLeakage.lower() == 'keep':
            libraries.append('HighDensityLowLeakage')
        
        if self.HighSpeed.lower() == 'keep':
            libraries.append('HighSpeed')
            
        if self.LowSpeed.lower() == 'keep':
            libraries.append('LowSpeed')
        
        if self.MediumSpeed.lower() == 'keep':
            libraries.append('MediumSpeed')
       
        if self.LowPower.lower() == 'keep':
            libraries.append('LowPower')

        return libraries 


FEW_SHOT_SUFFIX = """
If the user didn't specifiy a library, assume the HighDensity library. 
Give an explanation first for why you are choosing a specific library then output the JSON format. 
User input: {input}"""

USER_TEMPLATE = """            
If the user didn't specifiy a library, assume the HighDensity library. 
Give an explanation first for why you are choosing a specific library then output the JSON format
```json
"Explain": "<explain-your-choice>",
"HighDensity": "<keep-or-drop>",
"HighDensityLowLeakage": "<keep-or-drop>",
"HighSpeed": "<keep-or-drop>",
"LowSpeed": "<keep-or-drop>",
"MediumSpeed": "<keep-or-drop>",
"LowPower": "<keep-or-drop>",
``` 
{input}
"""

class SCLRouter(Agent):
    """
        Routes user questions to the relevant SCL view in the PDK
    """
    def __init__(self, config) -> None:
        super().__init__(context_winow=3048, output_tokens=512)
        
        self.config = config

        system = SCL_ROUTER_SYS_PROMPT
        
        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding standard cell library variants:"
            self.prompt = FewShotPromptTemplate(
                examples=scl_router_few_shot,
                example_prompt=PromptTemplate.from_template(
                    "User input: {input}\n{scl_explain}\nData sources: {scl_variant}"
                ),
                input_variables=["input"],
                prefix=system,
                suffix=FEW_SHOT_SUFFIX,
            )
            
        else:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", str(system)),
                    ("user", USER_TEMPLATE),
                ]
            )
        
        self.llm = config.lm_config.router_llm_model 
        # structured_llm = self.llm.with_structured_output(
        #     StandardCellLibrary, 
        #     include_raw=True
        # )

        # Define router 
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
            response = StandardCellLibrary(**content_json)

            # if out['parsed'] is None: 
            #     content = out['raw'].content
            #     content_json = parse_json_from_string(content)
            #     out['parsed']  = StandardCellLibrary(**content_json)

            # response = out['parsed']
            libraries = response.get_libraries()

            return {"scl_library": libraries}  
        else:
            return {"scl_library": ""}

    def scl_metric(self, gold, pred) -> int:
        return int(set(gold) == set(pred))

    
__all__ = [
  'SCLRouter',
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

    scl_router = SCLRouter(
       config=config
    )
    
    scl_prompt = scl_router.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?"
    )
    
    logger.info(f"CYAN: \n SCL Router Prompt \n {scl_prompt}") 

    scl_corect = 0
    for query in test_queries: 
        logger.info(f"CYAN: {query['input']}")

        routed_scl_variant = scl_router.route(
            {"question": query["input"]}
        )

        routed_scl_libraries = routed_scl_variant['scl_library']
        if set(routed_scl_libraries) == set(query["scl_variant"]): 
            scl_corect += 1 
    
        color = "GREEN" if set(routed_scl_libraries) == set(query["scl_variant"]) else "RED"
        logger.info(f"{color}: \n Cell Library:  {routed_scl_libraries}") 
        # logger.info(f"{color}: \n Routed Cell Library Explaination is {routed_scl_variant.Explain}")
        
    scl_router_accuracy = scl_corect / len(test_queries)
    logger.info(f"BLUE: \n Cell Library Router accuracy is {scl_router_accuracy}")


if __name__ == '__main__':
    main()