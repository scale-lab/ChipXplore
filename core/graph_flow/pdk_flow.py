import os 
import argparse
from enum import Enum

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import START, END, StateGraph

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.agents.routers.view_router import ViewRouter, View
from core.agents.routers.scl_router import SCLRouter
from core.agents.routers.lib_corner_router import LibCornerRouter
from core.agents.routers.techlef_corner_router import TechLefCornerRouter
from core.agents.selectors.table_selector import SchemaSelector 
from core.agents.generator.sql_generator import Decomposer
from core.agents.interpreter import Interpreter
from core.agents.refiner import RefinerSQL 
from core.graph_flow.states import PDKQueryState



class PDKNodes(Enum):
    ViewRouter = "ViewRouter"
    SCLRouter = "SCLRouter"
    TechLefCornerRouter = "TechLefCornerRouter"
    PVTRouter = "PVTRouter"
    TableSelector = "TableSelector"
    QueryGenerator = "QueryGenerator"
    QueryExecutor = "QueryExecutor"
    Refiner = "Refiner"
    Interpreter = "Interpreter"


class PDKGraph:
    def __init__(self, config: ChipQueryConfig, use_interpreter=False) -> None:
        
        self.config = config 
        self.use_interpreter = use_interpreter

        self.view_router = ViewRouter(
            config=config
        )

        self.scl_router = SCLRouter(
            config=config
        )

        self.techlef_router = TechLefCornerRouter(
            config=config
        )

        self.libcorner_router = LibCornerRouter(
            config=config,
        )

        self.selector = SchemaSelector(
            config=config
        )

        self.generator = Decomposer(
            config=config
        )
        
        self.refiner = RefinerSQL(
            config=config
        )

        self.interpreter = Interpreter(
            config=config
        )

        self.builder = StateGraph(PDKQueryState)
        
        self.builder.add_node(
            PDKNodes.ViewRouter.value, 
            self.view_router.route
        )

        self.builder.add_node(
            PDKNodes.SCLRouter.value, 
            self.scl_router.route
        )

        self.builder.add_node(
            PDKNodes.TechLefCornerRouter.value, 
            self.techlef_router.route
        )
        self.builder.add_node(
            PDKNodes.PVTRouter.value, 
            self.libcorner_router.route
        )
        self.builder.add_node(
            PDKNodes.TableSelector.value, 
            self.selector.select
        )

        self.builder.add_node(
            PDKNodes.QueryGenerator.value, 
            self.generator.decompose
        )

        self.builder.add_node(
            PDKNodes.QueryExecutor.value, 
            self.refiner.execute
        )
        self.builder.add_node(
            PDKNodes.Refiner.value, 
            self.refiner.refine
        )

        if use_interpreter: 
            self.builder.add_node(
                PDKNodes.Interpreter.value, 
                self.interpreter.interpret_pdk
            )

        self.builder.add_edge(START, PDKNodes.SCLRouter.value)
        self.builder.add_edge(START, PDKNodes.ViewRouter.value)
        self.builder.add_conditional_edges(
            PDKNodes.ViewRouter.value, self._should_continue, 
            [PDKNodes.PVTRouter.value, PDKNodes.TechLefCornerRouter.value, PDKNodes.TableSelector.value]
        )
        self.builder.add_edge(PDKNodes.PVTRouter.value, PDKNodes.TableSelector.value)
        
        self.builder.add_edge(
            [PDKNodes.TechLefCornerRouter.value, PDKNodes.SCLRouter.value], 
            PDKNodes.TableSelector.value
        )

        self.builder.add_edge(
            [PDKNodes.TableSelector.value],
            PDKNodes.QueryGenerator.value)

        self.builder.add_edge(PDKNodes.QueryGenerator.value, PDKNodes.QueryExecutor.value)
        self.builder.add_edge(PDKNodes.Refiner.value, PDKNodes.QueryExecutor.value)
        
        if use_interpreter:
            nodes =  [PDKNodes.Refiner.value, PDKNodes.Interpreter.value, END]
        else:
            nodes =  [PDKNodes.Refiner.value, END]

        self.builder.add_conditional_edges(
            PDKNodes.QueryExecutor.value, 
            self._should_refine, 
            nodes
        )

        if use_interpreter: 
            self.builder.add_edge(
                PDKNodes.Interpreter.value,
                END
            )
        self.graph = self.builder.compile()

        png_graph = self.graph.get_graph().draw_mermaid_png()
        with open(os.path.join("output/", "pdk_flow.png"), "wb") as f:
            f.write(png_graph)

    def forward(self, question) -> PDKQueryState:
        output = self.graph.invoke({"question": question}) 
        return output 
    
    def _should_refine(self, state: PDKQueryState):
        sql_executes = state.get("sql_executes")
        refine_iters = state.get("refine_iters", 0)
        if sql_executes or refine_iters >= self.config.flow_config.max_refine_iters:
            if self.use_interpreter: 
                return PDKNodes.Interpreter.value 
            else: 
                return END 
        else:
            return PDKNodes.Refiner.value

    def _should_continue(self, state: PDKQueryState):
        routed_view = state.get('view')
        if routed_view == View.TechLef.value:
            return PDKNodes.TechLefCornerRouter.value
        elif routed_view == View.Liberty.value:
            return PDKNodes.PVTRouter.value
        elif routed_view == View.Lef.value:
            return PDKNodes.TableSelector.value
        elif routed_view == "":
            return PDKNodes.TableSelector.value 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/design_graph_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--temperature', type=int, help='Model name', default=0)
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--partition', help="partition database", action='store_true', default=False)
    args = parser.parse_args() 

    output = args.output
    model = args.model 
    temperature = args.temperature
    partition = args.partition
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
            interpreter_lm=model,
            temperature=temperature,
        ),
        db_config=DatabaseConfig(
            partition=partition,
            in_mem_db=True,
            load_graph_db=False
        )
    )

    pdk_graph = PDKGraph(
        config=config,
        use_interpreter=True
    )

    # output = pdk_graph.forward(
    #     question="Retrieve the minimum width, minimum spacing, resistance, current density, and capacitance values for each metal layer in the PDK in the nom corner"
    # )

    # print("Result: \n")
    # print(output['result'])

    # output = pdk_graph.forward(
    #     question="What is the width of the and2_1 cell in the high density library ? "
    # )

    # print("Result: \n")
    # print(output['result'])

    output = pdk_graph.forward(
        question="What is the area of the and2_1 cell in the high density library ? "
    )

    print("Result: \n")
    print(output['result'])
    print(output['final_answer'])



if __name__ == '__main__':
    main()