
import os
import json
import argparse

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
)

from dotenv import load_dotenv
load_dotenv()

from core.agents.agent import Agent
from core.agents.few_shot.corner import lib_corner_few_shot
from core.eval.test_set import test_queries_lib
from core.graph_flow.states import PDKQueryState
from core.utils import get_logger, parse_temp, parse_voltage
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.agents.utils import parse_json_from_string



class CornerLib(BaseModel):
    """Route a user query to the most liberty corner."""
    explain: str = Field(description="Explaination of the operating condition choice")
    temperature: str = Field(description="Specifies temperature value, it should be a float value.")
    voltage: str = Field(description="Specifies voltage value, it should be a float value")


LIB_CORNER_SYS_PROMPT = """
You are an expert at routing a user questions to the appropriate operating conditions.

The operating conditions are specified by two values: 
- temperature: operating temperature, example values are: 
    - 25.0 (typical)
    - 40.0
    - 100.0
    - 140.0 
    - 150.0 
    
- voltage: operating voltage, example values are: 
    - 1.56
    - 1.6
    - 1.76
    - 1.8  (typical)
    - 1.89
    - 1.95
    - 2.1
    
If the user doesn't specify the operating conditoin, assume the typical corner at a 'temperature' value of '25.0' and 'voltage' value of '1.8'. 

Give an explanation first for why you are choosing a specific operating condition then output the JSON format:

```json 
{{
    "explain": <explaination-of-corner-choice>,
    "temperature": <temperature-value-float>,
    "voltage": <voltage-value-float>
}}
```
"""

LIB_FEW_SHOT_TEMPLATE = """User input: {input}
Operating Condtions:
```json
"explain": {explain},
"temperature": "{temperature}",
"voltage": "{voltage}"
```
"""

class LibCornerRouter(Agent):
    
    def __init__(self, config) -> None:
        super().__init__(context_winow=4048, output_tokens=512)
        self.config = config 

        system = LIB_CORNER_SYS_PROMPT
       
        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding operating conditions:"
            self.prompt = FewShotPromptTemplate(
                examples=lib_corner_few_shot,
                example_prompt=PromptTemplate.from_template(LIB_FEW_SHOT_TEMPLATE),
                input_variables=["input"],
                prefix=system,
                suffix="User input: {input}",
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
        #     CornerLib, 
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
                        print(f"[PVTRouter]: Exception Happened Retrying... {e}")
                out = full
            else: 
                out = self.router.invoke({"input": query})
            
            # if out['parsed'] is None: 
            #     content = out['raw'].content
            #     if type(content) == dict: 
            #         content = content["parameters"]
            #     print(content)
            #     parsed_content = json.loads(content)
            #     out['parsed']  = CornerLib(**parsed_content)
            
            print(out.content)
            json_content = parse_json_from_string(out.content)
            response = CornerLib(**json_content)
    
            return {"temp_corner": response.temperature, "voltage_corner": response.voltage} 
        else: 
            return {"temp_corner": "", "voltage_corner": ""} 

    def lib_corner_metric(self, gold, pred):
        if float(pred.temperature) == float(parse_temp(gold[0])) and \
        float(pred.voltage) == float(parse_voltage(gold[0])): 
            score = 1

        return score     


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
            partition=False,
            in_mem_db=True
        ),
    )


    # Router agents
    lib_corner_router = LibCornerRouter(
        config=config
    )
    
    lib_corner_prompt = lib_corner_router.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?"
    )
    logger.info(f"MAGENTA: \n Lib corner Router Prompt \n {lib_corner_prompt}") 
    
    lib_corner_correct = 0 
    
    for query in test_queries_lib: 
        logger.info(f"CYAN: {query['input']}")

        output = lib_corner_router.route(
            {"question": query["input"]}
        )

        # score = lib_corner_router.lib_corner_metric(
        #     gold=query['op_cond'],
        #     pred=CornerLib(explain="", temperature=output["temp_corner"], voltage=output["voltage_corner"])
        # )
        # lib_corner_correct += 1
        
        op_cond = f"Temperature: {output['temp_corner']}, Voltage: {output['voltage_corner']}"

        color = "GREEN" if True  else "RED"
        logger.info(f"{color}: \n Routed Operating Condition: {op_cond}")   
        # logger.info(f"{color}: \n Routed Operating Explain: {routed_op_cond.explain}")   

  
    lib_corner_acc = lib_corner_correct / len(test_queries_lib)

    logger.info(f"CYAN: \n Liberty-Corner Router accuracy is {lib_corner_acc}")

   

    
if __name__ == '__main__':
    main()