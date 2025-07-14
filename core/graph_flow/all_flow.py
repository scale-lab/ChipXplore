import re
import os 
import time 
import json
import argparse

from langchain import hub
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import tools_condition 
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from langchain_community.utilities import SQLDatabase
from langchain_community.graphs import Neo4jGraph
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from typing_extensions import Any, Annotated

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.graph_flow.design_flow import DesignGraph, DesignQueryState
from core.agents.interpreter import Interpreter
from core.graph_flow.pdk_flow import PDKGraph, PDKQueryState
from core.graph_flow.states import ChipQueryState
from core.graph_flow.reasoner import Reasoner, _PDK_QUERY_DESCR, _DESIGN_QUERY_DESCR, _FINISH_DESCR
from core.database.graphdb import URI, USER, PASSWORD
from core.stealth.encrypt import encrypt_data, decrypt_data


class ReActPlanner:
    def __init__(self, config) -> None:
        self.config = config 
        
        pdk_subgraph = PDKGraph(
            config=config
        )
        
        design_subgraph = DesignGraph(
            config=config
        )

        interpreter = Interpreter(
            config=config 
        )
        
        if config.flow_config.secure: 
            def pdk_query(
                state: ChipQueryState,
            ):
                messages = state.get("messages")
                last_message = messages[-1].content 
                json_object = self._extract_json(last_message)
                question = json_object["args"]
                if type(question) == dict:
                    question = question["question"]
                output = pdk_subgraph.forward(question)
                encrypted_result = encrypt_data(str(output["result"]))
                return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"pdk_query tool output: {encrypted_result}"}
        else:
            def pdk_query(
                state: ChipQueryState,
            ):
                messages = state.get("messages")
                last_message = messages[-1].content 
                json_object = self._extract_json(last_message)
                question = json_object["args"]
                if type(question) == dict:
                    question = question["question"]
                output = pdk_subgraph.forward(question)
                return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"pdk_query tool output: {str(output['result'])}"}

        if config.flow_config.secure: 
            def design_query(
                state: ChipQueryState, 
            ):
                messages = state.get("messages")
                last_message = messages[-1].content 
                json_object = self._extract_json(last_message)
                question = json_object["args"]
                if type(question) == dict:
                    question = question["question"]
                output = design_subgraph.forward(question)
                encrypted_result = encrypt_data(str(output["result"]))
                return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"design_query tool output: {encrypted_result}"}
        else:
            def design_query(
                state: ChipQueryState, 
            ):
                messages = state.get("messages")
                last_message = messages[-1].content 
                json_object = self._extract_json(last_message)
                question = json_object["args"]
                if type(question) == dict:
                    question = question["question"]
                output = design_subgraph.forward(question)
                return {"query": [output["refined_query"]], "result": [output["result"]], "messages": f"design_query tool output: {str(output['result'])}"}
    
        def finish(
            state: ChipQueryState, 
        ):
            output = interpreter.interpret(
                state=state
            )
            print("Final answer is: ", output)
            return {"final_answer": output}
        
        reasoner = Reasoner(
            config=config,
        )

        self.builder = StateGraph(ChipQueryState)
        self.builder.add_node("reasoner", reasoner.forward)
        self.builder.add_node("design_query", design_query)
        self.builder.add_node("pdk_query", pdk_query)
        self.builder.add_node("finish", finish)
        self.builder.add_edge(START, "reasoner")
        self.builder.add_conditional_edges(
            "reasoner",
            self._should_query
        )
        self.builder.add_edge("design_query", "reasoner")
        self.builder.add_edge("pdk_query", "reasoner")
        self.builder.add_edge("finish", END)

        self.graph = self.builder.compile()

        png_graph = self.graph.get_graph().draw_mermaid_png()
        with open(os.path.join("output", "react_graph.png"), "wb") as f:
            f.write(png_graph)

    
    def _extract_json(self, text):
        text = re.sub(r'```json\s*|\s*```', '', text).strip()

        json_matches = re.findall(r'\{(?:[^{}]|"(?:\\.|[^"])*"|\{(?:[^{}]|"(?:\\.|[^"])*")*\})*\}', text, re.DOTALL)
        
        if json_matches:
            json_content = json_matches[0]  # Get the last matched JSON object
            try:
                return json.loads(json_content)  # Parse JSON
            except json.JSONDecodeError as e:
                raise ValueError(f"Extracted JSON is invalid: Got Error {e} while parsing {json_content} from text {text}.")
        else:
            raise ValueError("No valid JSON found in the input.")

    def _should_query(self, state: ChipQueryState):
        messages = state.get("messages") 
        last_message = messages[-1].content
        json_object = self._extract_json(last_message)        
        if json_object["action"] == "design_query": 
            return "design_query"
        
        if json_object["action"] == "pdk_query":
            return "pdk_query"
        
        if json_object["action"] == "finish":
            return "finish"
         

    def forward(self, question: str) -> ChipQueryState:
        output = self.graph.invoke({"question": question}, {"recursion_limit": self.config.flow_config.graph_recursion_limit})
        return {'messages': output['messages'], 'final_answer': output['messages'][-1].content, 'query': output['query']}
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/design_graph_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--temperature', type=int, help='Model name', default=0)
    parser.add_argument('--partition', help="partition database", action='store_true', default=False)
    parser.add_argument('--secure', help="Enable secure framework", action='store_true', default=True)
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    args = parser.parse_args()
    
    output = args.output
    model = args.model 
    temperature = args.temperature
    partition = args.partition
    secure = args.secure
    few_shot = not args.wo_fewshot 

    if "gpt" in model and secure: 
        interpreter_lm = "llama3.3:70b"
    else:
        interpreter_lm = model 

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=few_shot,
            use_in_mem_db=True,
            graph_recursion_limit=10,
            secure=secure
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=interpreter_lm,
            temperature=temperature
        ),
        db_config=DatabaseConfig(
            partition=partition,
            in_mem_db=True
        )
    )

    react_planner = ReActPlanner(
        config=config,
    )

    # output = react_planner.forward(
    #     question="Compare the output pin capacitance of the mux4_1 cell between the high speed and medium speed libraries."
    # )
    # for m in output['messages']:
    #     m.pretty_print()

    # output = react_planner.forward(
    #     question="Compare the fall propagation delay of the mux2_1 cell between the high density and high density low leakage libraries. Assume an output load of 0.0005 and input rise time of 0.01. Output the fall propagation delay from the related input pin S to the output pin for both libraries."
    # )
    # for m in output['messages']:
    #     m.pretty_print()


    output = react_planner.forward(
        question="Compare the width of the nand2_1 cell in the High Density and the Medium Speed libraries"
    )
    
    for m in output['messages']:
        m.pretty_print()

    # output = react_planner.forward(
    #     question="Compare the height of the a31oi_1 cell in the High Speed, Low Speed, and Medium Speed libraries"
    # )
    
    # for m in output['messages']:
    #     m.pretty_print()

    # output = react_planner.forward(
    #     question="Which cell library has the smallest width for the mux4_1 cell ?"
    # )
    
    # for m in output['messages']:
    #     m.pretty_print()

    #######CORECT########
    # output = react_planner.forward(
    #     question="Compare the resistance per square unit of the met1 routing layer the between the three corners: nom, min, max"
    # )

    # for m in output['messages']:
    #     m.pretty_print()
    #####################

    # output = react_planner.forward(
    #     question="Compare the resistance of the via2 cut layer between the two operating corners: min, max"
    # )

    # for m in output['messages']:
    #     m.pretty_print()

    # output = react_planner.forward(
    #     question="Compare the pitch values for the met5 layer between the high density and high speed libraries for the nominal corner"
    # )

    # for m in output['messages']:
    #     m.pretty_print()


    # start_time = time.time()
    # output = react_planner.forward(question= "What is the number of flip-flops cells in the design?")
    # end_time = time.time()

    # print(f"Run time: {end_time - start_time}")
    # for m in output['messages']:
    #     m.pretty_print()

    # print(output)


if __name__ == '__main__':
    main()