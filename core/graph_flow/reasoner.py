import argparse 
from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages import AIMessage, HumanMessage

from dotenv import load_dotenv
load_dotenv()

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.agents.agent import Agent 
from core.graph_flow.states import ChipQueryState
from core.utils import get_logger
from core.eval.test_graph import test_design
from core.database.graphdb import URI, USER, PASSWORD
from core.database.sql import get_desc 
from core.graph_flow.design_flow import DesignGraph
from core.graph_flow.pdk_flow import PDKGraph


_PDK_QUERY_DESCR = """
Retrieves information from the PDK database such as information about standard cell libraries, library views, and operating conditions.
"""

# _PDK_QUERY_DESCR = """
# Retrieves information from the PDK database such as information about the process design kit,
# including standard cell libraries, library views, and operating conditions.

# PDK Database contains information about the process design kit, including standard cell libraries, library views, and operating conditions. This database is useful for questions about technology specifications, cell characteristics, and metal stack properties.
# The PDK includes 6 stanadrd cell libraries: 
#     [-] HighDensity: High Density (HD) Digital Standard Cells :
#        HighDensity Prefix is sky130_fd_sc_hd
#     [-] HighDensityLowLeakage: High Density Low Leakage (HDLL) Digital Standard Cell: 
#         HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
#     [-] HighSpeed: High Speed (HS) Digital Standard Cells: 
#         HighSpeed Prefix is sky130_fd_sc_hs
#     [-] LowSpeed: Low Speed (LS) Digital Standard Cells: 
#         LowSpeed Prefix is sky130_fd_sc_ls
#     [-] MediumSpeed: Medium Speed (MS) Digital Standard Cells
#         MediumSpeed Prefix is sky130_fd_sc_ms
#     [-] LowPower: Low Power (LP) Digital Standard Cells
#         LowPower Prefix is sky130_fd_sc_lp     

# Each library includes three views:
#     - Liberty view: 
#         - Contains the following charactersics of cells:
#         * Cell timing information (delay, gate capacitance, etc.)
#         * Input pin capacitances for clock and non-clock pins
#         * Overall cell area (as a single value, not dimensions)
#         * Input and output pin timing information (transition time, propagation delay, internal power)

#     - Lef view:
#         - Contains physical layout information of cells, including:
#         * Exact width and height of each cell
#         * Pin physical information (layers, pin rectangles and their coordinates)
#         * Pins antenna gate area
#         * Antenna ratios for input and output pins
#         * Power and ground pin names in the layout
#         * Cell obstruction shapes and their layers
    
#     - TechnologyLef:
#         - Contains process-specific design rules and technology information at different operating corners, including:
#         * Metal (routing) and via (cut) layer rules (minimum width, pitch, thickness, offset)
#         * Available routing and cut layers in the PDK and their antenna area ratios
#         * Metal layer properties (pitch, width, spacing, offset)
#         * Via layer (cut layer) specifications
            
# """

_DESIGN_QUERY_DESCR = """
Retrieves information from the design database.
"""



# _DESIGN_QUERY_DESCR = """
# Retrieves information from the design database. It contains the following information: 
#     - Design: Defines the design node including design name, die area, and physcial design stage (floorplan, placement, cts, routing).
#     - Pin: Defines input and output ports of the design, including pin names, direction, width, height, layer used for drawing the pin, pin signal type (whether it is a signal, power, or ground pin), and x,y location.
#     - Cell: Defines cells in the design including their area, including their name, height, width, area, power, whether cell is sequential, or physical only, or buffer, or inverter cell, and location.
#     - InternalCellPin: Defines information about the design cell pins including output pin transition, pin slack, pin rise arrival, pin fall arrival time, and input pin capacitances. 
#     - Net: Defines nets in the design including their name, capacitance, resistance, coupling, fanout, length, and net signal type (whether it is power, ground, or signal net).
#     - Segments: Defines metal layers used for routing the nets in the design like clock nets, specific signal nets, power and ground nets. 
# """


_FINISH_DESCR = """
Interprets the results of the tool calls and Returns a natural language response to the user. 
"""

PLANNER_SYS_PROMPT = """
You are a helpful assistant tasked with using pdk_query, design_query, finish tools to answer user questions related to process design kits (PDKs) and hardware designs. 
Your task is to determine whether to directly query a database or to create and execute a query plan to answer user question.

You have access to three tools:
1. pdk_query:
    - Retrieves information from the PDK database such as information about the process design kit, including standard cell libraries, library views, and operating conditions. 
        PDK Database contains information about the process design kit, including standard cell libraries, library views, and operating conditions. This database is useful for questions about technology specifications, cell characteristics, and metal stack properties.
        The PDK includes 6 stanadrd cell libraries: 
            [-] HighDensity: High Density (HD) Digital Standard Cells :
            HighDensity Prefix is sky130_fd_sc_hd
            [-] HighDensityLowLeakage: High Density Low Leakage (HDLL) Digital Standard Cell: 
                HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
            [-] HighSpeed: High Speed (HS) Digital Standard Cells: 
                HighSpeed Prefix is sky130_fd_sc_hs
            [-] LowSpeed: Low Speed (LS) Digital Standard Cells: 
                LowSpeed Prefix is sky130_fd_sc_ls
            [-] MediumSpeed: Medium Speed (MS) Digital Standard Cells
                MediumSpeed Prefix is sky130_fd_sc_ms
            [-] LowPower: Low Power (LP) Digital Standard Cells
                LowPower Prefix is sky130_fd_sc_lp     

        Each library includes three views:
            - Liberty view: 
                - Contains the following charactersics of cells:
                * Cell timing information (delay, gate capacitance, etc.)
                * Input pin capacitances for clock and non-clock pins
                * Overall cell area (as a single value, not dimensions) **Does NOT have width or height information. Width and height information are found in the Lef View.**
                * Input and output pin timing information (transition time, propagation delay, internal power)

            - Lef view:
                - Contains physical layout information of cells, including:
                    * Exact width and height of each cell
                    * Pin physical information (layers, pin rectangles and their coordinates)
                    * Pins antenna gate area
                    * Antenna ratios for input and output pins
                    * Power and ground pin names in the layout
                    * Cell obstruction shapes and their layers
            
            - TechnologyLef:
                - Contains process-specific design rules and technology information at different operating corners, including:
                * Metal (routing) and via (cut) layer rules (minimum width, pitch, thickness, offset)
                * Available routing and cut layers in the PDK and their antenna area ratios
                * Metal layer properties (pitch, width, spacing, offset)
                * Via layer (cut layer) specifications

    
        [NOTE]: 
            - Cell names in the PDK are prefixed with library.
            - For example cells in high density are prefixed with 'sky130_fd_sc_hd__'. 
            - High speed are prefixed with 'sky130_fd_sc_hs__'. 
            - High density low leakage are prefixed with 'sky130_fd_sc_hdll__'
            - When querying the PDK chain for information about a specific cell, make sure the cell name prefix matches the library. 
            - **If a query explicitly asks for a cross-library comparison, it must be sent as is.**

    - Arguments: 
        - question: string, specifies question to ask for the design database 
        
2. design_query:
    - Retrieves information from the design database. It contains the following information: 
        - Design: Defines the design node including design name, die area, and physcial design stage (floorplan, placement, cts, routing).
        - Pin: Defines input and output ports of the design, including pin names, direction, width, height, layer used for drawing the pin, pin signal type (whether it is a signal, power, or ground pin), and x,y location.
        - Cell: Defines cells in the design including their area, including their name, height, width, area, power, whether cell is sequential, or physical only, or buffer, or inverter cell, and location.
        - InternalCellPin: Defines information about the design cell pins including output pin transition, pin slack, pin rise arrival, pin fall arrival time, and input pin capacitances. 
        - Net: Defines nets in the design including their name, capacitance, resistance, coupling, fanout, length, and net signal type (whether it is power, ground, or signal net).
        - Segments: Defines metal layers used for routing the nets in the design like clock nets, specific signal nets, power and ground nets. 

    - Arguments: 
        - question: string, specifies question to ask for the design database 

        
3. finish:
    - Interprets the results of the previous tool calls and Returns a natural language response to the user. 
    - Takes no arguments 
    
Each step in a plan should be one of three actions:
1. 'pdk_query': For querying the PDK
2. 'design_query': For querying the Design
3. 'finish': For formulating the final answer. 


[Requirements]
- **DO NOT decompose queries by standard cell libraries.**
- If the question doesn't not require decomposition, you must use it the question as is in your function call. 
- If the question explicitly asks for total values (e.g., total area, total number of cells), or largest/smallest value **DO NOT decompose the query. Instead, route it directly to a single design_query or pdk_query WITHOUT rephrasing the question.**
- If the question requires querying both PDK and design databases, decompose the question and create a detailed plan to handle subqueries and combining results.
- Don't query the databases for information on all individual entries unless retrieving aggregated statistics such as total cell area.
- You must end the tool calling once you have called the finish tool call..  
- You must use the finish tool to formulate the final answer.
- Output one action at a time.  

[Additional Requirements for Efficiency]
- For queries that involve multiple cells or cell types, ALWAYS use aggregate queries instead of asking for individual cells.
- When calculating area or other statistics about groups of cells:
  * Use queries like "What is the total area of all buffer cells in the design?" instead of "What are all buffer cells and their areas?"
  * Use queries like "How many buffer cells of each type are in the design?" to get counts by type
  * Ask for summary statistics like "What is the count and total area of buffer cells in the design grouped by cell type?"
- When comparing cells or calculating potential changes, use specific aggregation queries rather than retrieving all individual data.
- Context window management is critical - avoid queries that return extensive lists of individual cells or detailed properties.


You must output Your action in the following json format: 

```json
{
    "action": "<one-of-the-three-actions>",
    "args": "<action-arguments>"
}
```
"""

#- If the question asks questions about multiple standard cell libraries or operating conditions, you must decompose it.


#
#


class Reasoner(Agent):

    def __init__(self, config: ChipQueryConfig) -> None:
        super().__init__()
        self.config = config
        self.system_prompt = PLANNER_SYS_PROMPT
        self.system_msg = SystemMessage(content=PLANNER_SYS_PROMPT)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{user_question}")
        ])
       
        self.llm = config.lm_config.planner_llm_model

    def forward(self, state: ChipQueryState):
        question = state.get("question")
        messages = state.get("messages", [])
        if len(messages) == 0:  
            message = HumanMessage(content=question)
            messages.append(message)
            
        if "deepseek-chat" in self.config.lm_config.planner_lm_name: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.llm.stream([self.system_msg] + messages)
                    full = next(stream)
                    for chunk in stream:
                        full += chunk
                    full
                    received = True 
                except ValueError as e:
                    print(f"[Reasoner]: Exception Happened Retrying... {e}")
            result = [full] 
        else: 
            result = [self.llm.invoke([self.system_msg] + messages)]
        return {"messages": result}



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

    reasoner = Reasoner(
        config=config
    )
    
    state = ChipQueryState()
    state['question'] = "How many cells are in the high density library ?"
    output = reasoner.forward(state)

    for m in output['messages']:
        m.pretty_print()

    state = ChipQueryState()
    state['question'] = "How many flip flop cells are in the design ?"
    output = reasoner.forward(state)

    for m in output['messages']:
        m.pretty_print()

    state = ChipQueryState()
    state['question'] = "What would be the total area increase of replacing all flip-flop cells in the design with the scan enabled flip flop cell from the high density library ?"
    output = reasoner.forward(state)

    for m in output['messages']:
        m.pretty_print()


if __name__ == '__main__':
    main()