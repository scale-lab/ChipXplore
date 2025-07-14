
import os
import ast
import json
import argparse
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
)
from typing import List


from dotenv import load_dotenv
load_dotenv()

from core.agents.agent import Agent
from core.agents.few_shot.corner import techlef_corner_router_few_shot, lib_corner_few_shot
from core.eval.test_set import test_queries_tlef
from core.graph_flow.states import PDKQueryState
from core.utils import get_logger
from core.agents.utils import parse_json_from_string_list
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig


# Data model
class CornerTechLef(BaseModel):
    """Route a user query to the most relevant techlef corner."""
    explain: str = Field(description="Explanaiton for the corner choice")
    corner: List[Literal["min", "max", "nom"]] = Field(
        ...,
        description="Given a user question choose which operating corner would be most relevant for answering their question",
    )


TECHLEF_CORNER_SYS_PROMPT = """
You are an expert at routing a user questions to the appropriate techlef corner.

There are three corners for the techlef: 
- min 
- nom
- max

User could specifiy multiple corners in the same question. 

If the user doesn't specify the a corner, assume the nominal corner 'nom'.     

Give an explanation first for why you are choosing a specific corner then output the JSON format.

```json
{{
    "explain": "<explain-your-choice>",
    "corner": "[<techlef-corners-(min-nom-max)>]"
}}
```
 
'corner' should be a list of strings.

"""

TECHLEF_FEW_SHOT_TEMPLATE = """User input: {input}
```json
    "explain": "{explain}",
    "corner": "{corner}"
```
"""

TECHLEF_ZSHOT_TEMPLATE="""
If a user didn't specify a corner, assume the 'nom' corner.
Give an explanation first for why you are choosing a specific corner then output the JSON format

```json
'explain': "<explain-your-choice>",
'corner': [<techlef-corners-(min-nom-max)>]
```

'corner' should be a list of strings.

{input}                
"""


class TechLefCornerRouter(Agent):
    def __init__(self, config) -> None:
        super().__init__(context_winow=3048, output_tokens=512)
        self.config = config 
        system = TECHLEF_CORNER_SYS_PROMPT
       
        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding techlef corner:"
            self.prompt = FewShotPromptTemplate(
                examples=techlef_corner_router_few_shot,
                example_prompt=PromptTemplate.from_template(TECHLEF_FEW_SHOT_TEMPLATE),
                input_variables=["input", "corner"],
                prefix=system,
                suffix="User input: {input}",
            )
            
        else:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", str(system)),
                    ("user", TECHLEF_ZSHOT_TEMPLATE),
                ]
            )

        self.llm = config.lm_config.router_llm_model        
        # structured_llm = self.llm.with_structured_output(
        #     CornerTechLef, 
        #     include_raw=True
        # )

        self.router = self.prompt | self.llm
        
    def route(self, state: PDKQueryState):
        if self.config.flow_config.use_router: 
            query = state.get("question")

            if "deepseek-chat" in self.config.lm_config.router_llm_model: ## Hacky fix to unreliable API
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
           
            json_content = parse_json_from_string_list(out.content)
         
            try: 
                corner = ast.literal_eval(json_content["corner"])
            except:
                corner = json_content["corner"]
            
            response = CornerTechLef(explain=json_content["explain"], corner=corner)
            # response = CornerTechLef(explain=json_content["explain"], corner=json_content["corner"])
            # if out['parsed'] is None: 
            #     content = out['raw'].content
            #     parsed_content = json.loads(content)
            #     out['parsed']  = CornerTechLef(**parsed_content)

            # response = out['parsed']

            # print(response.corner)
            return {"techlef_op_cond": response.corner}
        else: 
            return {"techlef_op_cond": ""}
        

    def compute_score(self, gold, pred):
        gold_corner = set(gold) 
        pred_corner = set(pred) 
        return int(gold_corner == pred_corner)



__all__ = [
  'LibCornerRouter',
  'TechLefCornerRouter'
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
            in_mem_db=True,
            load_graph_db=False
        ),
    )

    techlef_corner_router = TechLefCornerRouter(
        config=config
    )
    
    techlef_corner_prompt = techlef_corner_router.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?"
    )
    logger.info(f"CYAN: \n Techlef corner Router Prompt \n {techlef_corner_prompt}") 
    
    techlef_corner_correct = 0 
    for query in test_queries_tlef: 
        logger.info(f"CYAN: {query['input']}")

        techlef_corner = techlef_corner_router.route(
            {"question": query["input"]}
        )
        score = techlef_corner_router.compute_score(
            pred=techlef_corner,
            gold=query['op_cond']
        )
        techlef_corner_correct+=score
                
        color = "GREEN" if score  else "RED"
        logger.info(f"{color}: \n Routed Operating Condition: {techlef_corner}")
        # logger.info(f"{color}: \n Routed Operating Explain: {techlef_corner.}")

        break 

    techlef_corner_acc = techlef_corner_correct / len(test_queries_tlef)

    logger.info(f"CYAN: \n TechLef-Corner Router accuracy is {techlef_corner_acc}")

    # techlef_corner = techlef_corner_router.route(
    #     {"question": "What is the maximum resistance of cut layers at the min corner?"}
    # )
    
    # logger.info(f"YELLOW: Routed Operating Condition, {techlef_corner}")


if __name__ == '__main__':
    main()