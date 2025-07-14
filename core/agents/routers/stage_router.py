import time 
import argparse
from typing import List
from enum import Enum

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
    ChatPromptTemplate
)

from core.agents.agent import Agent
from core.agents.few_shot.stage import stage_few_shot
from core.eval.test_graph import test_design
from core.graph_flow.states import DesignQueryState 
from core.agents.utils import parse_json_from_string
from core.utils import get_logger
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig

from dotenv import load_dotenv
load_dotenv()


class StageType(Enum):
    FLOORPLAN = 1
    PLACEMENT = 2
    CTS = 3
    ROUTING = 3
 
    @classmethod
    def from_string(cls, s):
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError(f"'{s}' is not a valid {cls.__name__}")


class Stage(BaseModel):
    """Route a user query to the design stage."""
    explain: str = Field(description="Explaination of stage choice", default='')
    floorplan: str = Field(description="Specifies whether to keep ('keep') or drop ('drop') the floorplan stage", default='drop')
    placement: str = Field(description="Specifies whether to keep ('keep') or drop ('drop') the placement stage",default='drop')
    cts: str = Field(description="Specifies whether to keep ('keep') or drop ('drop') the Clock Tree Synthesis (CTS) stage", default='drop')
    routing: str = Field(description="Specifies whether to keep ('keep') or drop ('drop') the routing stage, routing stage is the final stage it contains the final design information.", default='keep')

    def get_stages(self):
        stages = []
        if self.floorplan.lower() == 'keep':
            stages.append('floorplan')
        
        if self.placement.lower() == 'keep':
            stages.append('placement')
        
        if self.cts.lower() == 'keep':
            stages.append('cts')

        if self.routing.lower() == 'keep':
            stages.append('routing')
        
        return stages 


STAGE_ROUTER_SYS_PROMPT = """
You are an expert at routing a user questions to the appropriate physical design stage(s).

There are five physical design stages: 

[1] floorplan
[2] placement
[3] cts
[4] routing


[Instructions]
- ALWAYS route to the 'routing' stage by default for ANY question that doesn't explicitly mention a specific stage name. This is because 'routing' stage contains the final and most up-to-date design information, including all information from previous stages.
- Even if the question asks about information that is initially created or defined in earlier stages (like floorplan or placement), you MUST still route to 'routing' stage unless the question explicitly mentions an earlier stage by name.
- Only route to a specific earlier stage if the question explicitly mentions that stage by name (e.g., "in the floorplan stage").
- If a question explicitly asks to compare multiple stages, route it to only the mentioned stages.

[Requirements]
1. If a stage is relevant to the user question, mark it as "keep".
2. If a stage is completely irrelevant to the user question, mark it as "drop".

You must follow the [Instructions] and the [Requirements].

Give a brief explanation first for why you are choosing a specific stage then output the JSON format. 
```json 
{{
    "explain": "<explain-your-choice>",
    "floorplan": "<keep-or-drop>",
    "placement": "<keep-or-drop>",
    "cts": "<keep-or-drop>",
    "routing": "<keep-or-drop>"
}}
```
""" 

FEW_SHOT_TEMPLATE = """User input: {input}
Routed Stage: {stage}
"""





class StageRouter(Agent):

    def __init__(self, config):
        super().__init__(context_winow=3048, output_tokens=512)
        self.config = config 
        system = STAGE_ROUTER_SYS_PROMPT
        
        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding stage:"
            self.prompt = FewShotPromptTemplate(
                examples=stage_few_shot,
                example_prompt=PromptTemplate.from_template(FEW_SHOT_TEMPLATE),
                input_variables=["input", "stage"],
                prefix=system,
                suffix="User input: {input}",
            )
        else: 
            self.prompt = ChatPromptTemplate.from_messages([
                    ("system", str(system)),
                    ("user", "{input}"),
                ]
            )
            
        self.llm = config.lm_config.router_llm_model
        # structured_llm = self.llm.with_structured_output(
        #     Stage, 
        #     include_raw=True,
        # )
        self.router = self.prompt | self.llm

    def route(self, state: DesignQueryState):

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
                        print(f"Exception Happened Retrying... {e}")
                out = full 
            else: 
                out = self.router.invoke({"input": query})
     
            content_json = parse_json_from_string(out.content)                
            response  = Stage(**content_json)
        
            return {"stage": response.get_stages()}
        else:
            return {"stage": ""}


    def stage_metric(self, gold_stages, pred_stages, relaxed=False): 
        if len(gold_stages) > 1: 
            return set(gold_stages) == set(pred_stages)
        
        if not relaxed: 
            if len(pred_stages) != len(gold_stages):
                return 0 
        
        gold = StageType.from_string(gold_stages[0])
        
        score = []
        for pred in pred_stages: 
            pred_value = StageType.from_string(pred).value
            score.append(pred_value >= gold.value)
        
        return all(score)


__all__ = [
  'StageRouter',
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
            use_router=True,
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

    stage_router = StageRouter(
       config=config
    )
   
    stage_prompt = stage_router.prompt.format(input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?")

    logger.info(f"CYAN: \n Stage Router Prompt \n {stage_prompt}") 

    correct = 0
    for query in test_design: 
        logger.info(f"CYAN: {query['input']}")
        
        stage = stage_router.route({"question": query['input']})
        routed_stages = stage["stage"]
        
        score = stage_router.stage_metric(
            gold_stages=query['stage'], 
            pred_stages=routed_stages
        )
        correct += score
            
        color = "GREEN" if score else "RED"
        logger.info(f"{color}: \n Stage  is {routed_stages}")


    stage_accuracy = correct / len(test_design)
    logger.info(f"CYAN: \n Stage accuracy is {stage_accuracy}")



if __name__ == '__main__':
    main()