"""Selects relevant nodes from a graph database schema 
"""

import os
import re
import json
import time 
import logging
import argparse


from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
    ChatPromptTemplate
)
from langchain_core.pydantic_v1 import BaseModel, Field

from core.database.graphdb import get_node_descr, get_relationship_descr_verbose, get_relationship_descr
from core.agents.utils import parse_json_from_string
from core.eval.test_graph import test_design
from core.agents.few_shot.node_selector import node_few_shot
from core.agents.routers.router import StageRouter
from core.agents.agent import Agent
from core.graph_flow.states import DesignQueryState
from core.utils import get_logger
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig


class SelectedNodes(BaseModel):
    Design: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Design' node."
    )
    Port: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Port' node."
    )
    Cell: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Cell' node."
    )
    CellInternalPin: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'CellInternalPin' node."
    )
    Net: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Net' node."
    )
    Segment: str = Field(
        default="keep",
        description="Specifies whether to keep ('keep') or drop ('drop') the 'Segment' node."
    )

    def get_selected_nodes(self):
        nodes = []
        if self.Design.lower() == 'keep':
            nodes.append('Design')
            
        if self.Port.lower() == 'keep':
            nodes.append('Port')
        
        if self.Cell.lower() == 'keep':
            nodes.append('Cell')
        
        if self.CellInternalPin.lower() == 'keep':
            nodes.append('CellInternalPin')
            
        if self.Net.lower() == 'keep':
            nodes.append('Net')
            
        if self.Segment.lower() == 'keep':
            nodes.append('Segment')
        
        return nodes


NODE_SELECTOR_SYS_PROMPT = """As an experienced and professional graph database administrator, your task is to analyze a user question
and a database schema to provide relevant information. The database schema consists of node
descriptions, each containing multiple attribute descriptions. Your goal is to identify the relevant
nodes based on the user question.

[Instruction]
1. Discard any node that is not related to the user question. 
2. Always mark "Design" node as 'keep'
3. The output must be in JSON format: 

```json 
{{
"Design": "keep",
"Port": "<keep-or-drop>",
"Cell": "<keep-or-drop>",
"CellInternalPin": "<keep-or-drop>",
"Net": "<keep-or-drop>",
"Segment": "<keep-or-drop>"
}}
```

4. You must mark all nodes in your JSON output. 

[Requirements]
1. If a node is relevant to the user question, mark it as "keep". 
2. If a node is completely irrelevant to the user question, mark it as "drop". 
3. If you are unsure about the node relevance, still mark it as "keep". 
4. If you need data from Node A and Node C, and Node B connects them using the edge relationships, you must include Node B in your selection.
5. If you choose two nodes that don't have edge connection between them, you should also choose the intermediary node that connects them. 
6. **CRITICAL**: If you choose two nodes that don't have a direct edge connection between them, you MUST also include all intermediary nodes that connect them. Failing to do this will result in an invalid selection.

Below is the schema description for the nodes. Use the edge relationships to determine connection between nodes: 
[Schema]
{desc_str}

[Edges]
{edges}
""" 

NODE_SELECTOR_SUFFIX = """Think step by step about the needed nodes, then output your answer in json format. Give your answer in the same format as the given examples: 

User input {input} 
"""

FEW_SHOT_TEMPLATE = """User input: {input}
Selected Nodes: {nodes}
"""

class NodeSelector(Agent):
    
    def __init__(self, config):
        super().__init__(context_winow=5028, output_tokens=1048)

        self.config = config 
        system = NODE_SELECTOR_SYS_PROMPT
        
        if config.flow_config.few_shot: 
            system += "Here are some examples for user input and their corresponding selected nodes:"
            self.prompt = FewShotPromptTemplate(
                examples=node_few_shot,
                example_prompt=PromptTemplate.from_template(FEW_SHOT_TEMPLATE),
                input_variables=["input", "nodes"],
                prefix=system,
                suffix="Think step by step about the needed nodes, then output your answer in json format, considering [Requirements]. \n User input: {input}",
            )
        else: 
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system),
                    ("human", "Think step by step about the needed nodes, then output your answer in json format, considering [Requirements]. \n {input}"),
                ]
            )

        self.node_descr = get_node_descr()
        self.edges = get_relationship_descr_verbose()

        self.llm = config.lm_config.selector_llm_model 
        self.selector = self.prompt | self.llm

    def select(self, state: DesignQueryState):
        if self.config.flow_config.use_selector: 
            query = state.get("question")
            
            if "deepseek-chat" in self.config.lm_config.selector_lm_name: ## Hacky fix to unreliable API
                received = False
                while not received: 
                    try: 
                        stream = self.selector.stream({
                            'input': query, 
                            'desc_str': self.node_descr, 
                            'edges': self.edges,
                        })
                        
                        full = next(stream)
                        for chunk in stream:
                            full += chunk
                        full
                        received = True 
                    except ValueError as e:
                        print(f"[Selector]: Exception Happened Retrying... {e}")
                output = full 
            else: 
                output = self.selector.invoke({
                    'input': query, 
                    'desc_str': self.node_descr, 
                    'edges': self.edges,
                })
          

            print("Selector output: ", output)
            if type(output) != str: 
                output = output.content
            
            print("Selector output: ", output)

            response = parse_json_from_string(output)
            selected_nodes = SelectedNodes(**response).get_selected_nodes()
            
            node_descr = get_node_descr(selected_nodes)
            edges = get_relationship_descr_verbose(selected_nodes)

            return {"nodes": selected_nodes, "node_descr": node_descr, "edges": edges}
        else: 
            return {"nodes": "", "node_descr": self.node_descr, "edges": self.edges}

    def compute_exact_accuracy(self, pred_tables, ground_truth):
        is_exact = set(ground_truth)==(set(pred_tables))           
        return is_exact 

    def compute_subset_accuracy(self, pred_tables, ground_truth):
        if pred_tables is None:
            return 0 
        is_subset = set(ground_truth).issubset(set(pred_tables))     
        return is_subset 



__all__ = [
  'NodeSelector'
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--use_router', action='store_true', default=False)
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/selector_eval.log')
    args = parser.parse_args()

    output = args.output
    model = args.model 
    use_router = args.use_router
    few_shot = not args.wo_fewshot
    
    logger = get_logger(output)

    logger.info(f"CYAN: LLM Agent is {model}") 
    logger.info(f"CYAN: Few Shot Set to {few_shot}") 

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=few_shot,
            use_in_mem_db=True,
            graph_recursion_limit=10,
            secure=True
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=model,
            temperature=0
        ),
        db_config=DatabaseConfig(
            partition=True,
            in_mem_db=True
        )
    )

    node_descr = get_node_descr()
    relationship = get_relationship_descr()
        
    stage_router = StageRouter(
       config=config
    ) 
    
    selector = NodeSelector(
        config=config
    )
    
    stage_router_prompt = stage_router.prompt.format(input="Which cell has the largest area in the design ?")
    selector_prompt = selector.prompt.format(
        input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?", 
        desc_str=node_descr, 
        edges=relationship, 
    )

    logger.info(f"MAGENTA: Stage Router Prompt is {stage_router_prompt}") 
    logger.info(f"MAGENTA: Selector Prompt for liberty is {selector_prompt}") 

    stage_correct = 0
    selector_exact_correct = 0 
    selector_relaxed_correct = 0
    
    for query in test_design:

        logger.info(f"CYAN: {query['input']}")        
     
        if use_router: 
            stage = stage_router.route({"question": query["input"]})
            routed_stages = stage.get_stages()
        else:
            routed_stages = query['stage']

        stage_score = stage_router.stage_metric(query['stage'], routed_stages) 
        color = 'GREEN' if stage_score else 'RED'
        logger.info(f"{color}: Routed Stage: {routed_stages}")
        
        output = selector.select({
            "question": query["input"],
            "node_descr": node_descr,
            "edges": relationship
        })
        
        selected_nodes = output["nodes"]

        exact_score = selector.compute_exact_accuracy(
            selected_nodes, 
            query["selected_nodes"]
        )
        relaxed_score = selector.compute_subset_accuracy(
            selected_nodes, 
            query["selected_nodes"]
        )

        color = 'GREEN' if relaxed_score else 'RED'
        logger.info(f"{color}: Selected Nodes are {selected_nodes}")

        stage_correct += stage_score
        selector_exact_correct += 1 if exact_score else 0 
        selector_relaxed_correct += 1 if relaxed_score else 0

        time.sleep(1)

    stage_router_accuracy = stage_correct / len(test_design)
    selector_exact_accuracy = selector_exact_correct / len(test_design)
    selector_relaxed_accuracy = selector_relaxed_correct / len(test_design)

    logger.info(f"BLUE: Stage Router Accuracy is {stage_router_accuracy}")
    logger.info(f"BLUE: Selector Exact Accuracy is {selector_exact_accuracy}")
    logger.info(f"BLUE: Selector Subset Accuracy is {selector_relaxed_accuracy}")


if __name__ == '__main__':
    main()