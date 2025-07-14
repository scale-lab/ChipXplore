import os 
import argparse
from enum import Enum

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import START, END, StateGraph
from langchain_community.graphs import Neo4jGraph

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.agents.routers.stage_router import StageRouter
from core.agents.selectors.node_selector import NodeSelector 
from core.agents.generator.cypher_generator import CypherGenerator
from core.agents.refiner import RefinerCypher 
from core.graph_flow.states import DesignQueryState
from core.database.graphdb import URI, USER, PASSWORD


class DeisgnNodes(Enum):
    StageRouter = "StageRouter"
    NodeSelector = "NodeSelector"
    CypherGenerator = "CypherGenerator"
    Refiner = "Refiner"
    Executor = "Executor"


class DesignGraph:

    def __init__(self, config: ChipQueryConfig) -> None:
        
        self.config = config 
        self.stage_router = StageRouter(
            config=config
        )
        self.selector = NodeSelector(
            config=config
        )
        self.generator = CypherGenerator(
            config=config
        )
        self.refiner = RefinerCypher(
            config=config
        )
        # Nodes 
        self.builder = StateGraph(DesignQueryState)
        self.builder.add_node(
            DeisgnNodes.StageRouter.value, 
            self.stage_router.route
        )
        self.builder.add_node(
            DeisgnNodes.NodeSelector.value, 
            self.selector.select
        )
        self.builder.add_node(
            DeisgnNodes.CypherGenerator.value, 
            self.generator.generate
        )
        self.builder.add_node(
            DeisgnNodes.Executor.value, 
            self.refiner.execute
        )
        self.builder.add_node(
            DeisgnNodes.Refiner.value, 
            self.refiner.refine
        )

        # Edges 
        self.builder.add_edge(START, DeisgnNodes.StageRouter.value)
        self.builder.add_edge(START, DeisgnNodes.NodeSelector.value)
        self.builder.add_edge([DeisgnNodes.NodeSelector.value, DeisgnNodes.StageRouter.value], DeisgnNodes.CypherGenerator.value)
        self.builder.add_edge(DeisgnNodes.CypherGenerator.value, DeisgnNodes.Executor.value)
        self.builder.add_edge(DeisgnNodes.Refiner.value, DeisgnNodes.Executor.value)

        self.builder.add_conditional_edges(
            DeisgnNodes.Executor.value, 
            self._should_refine, 
            [DeisgnNodes.Refiner.value, END]
        )
        self.graph = self.builder.compile()
        
        png_graph = self.graph.get_graph().draw_mermaid_png()
        with open(os.path.join("output/", "design_graph.png"), "wb") as f:
            f.write(png_graph)

    def _should_refine(self, state: DesignQueryState):
        cypher_executes = state.get("cypher_executes")
        refine_iters = state.get("refine_iters")

        if cypher_executes or refine_iters == self.config.flow_config.max_refine_iters:
            return END 
        else:
            return DeisgnNodes.Refiner.value

    def forward(self, question) -> DesignQueryState:
        output = self.graph.invoke({"question": question})
        return output



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/design_graph_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--temperature', type=int, help='Model name', default=0)
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    args = parser.parse_args()
    
    output = args.output
    model = args.model 
    temperature = args.temperature
    few_shot = not args.wo_fewshot
   
    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=True,
            use_in_mem_db=True
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            temperature=temperature,
        ),
        db_config=DatabaseConfig(
            partition=False,
            in_mem_db=True
        )
    )
 
    design_graph = DesignGraph(
       config=config
    )

    output = design_graph.forward(
        question="How many unique cells are in the design ?"
    )

    print(output["cypher_query"])
    print(output["refined_query"])
    print(output["error"])
    print(output["refine_iters"])



if __name__ == '__main__':
    main()