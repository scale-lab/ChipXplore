
import os
import argparse

from typing import List
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

from dotenv import load_dotenv
load_dotenv()

from core.agents.agent import Agent
from core.agents.utils import parse_json_from_string
from core.agents.few_shot import view_router_few_shot, scl_router_few_shot, techlef_corner_router_few_shot, lib_corner_few_shot
from core.eval.test_set import test_queries, test_queries_tlef, test_queries_lib, test_queries_lef
from core.eval.test_graph import test_design
from core.eval.test_design_pdk import test_design_pdk

from core.utils import get_logger, parse_temp, parse_voltage


class Database(BaseModel):
    """Route a user question to the relevant database."""
    explain: str = Field(description="Explaination of database choice")
    pdk_db: str = Field(description="Use PDK Database")
    design_db: str = Field(description="Use Design Database")

    def get_databases(self):
        dbs = []
        if self.pdk_db.lower() == 'keep':
            dbs.append('pdk')
        
        if self.design_db.lower() == 'keep':
            dbs.append('design')
    
        return dbs 


DB_ROUTER_SYS_PROMPT = """
You are an AI expert specializing in semiconductor design and process design kits (PDKs). Your task is to analyze user questions and route them to the appropriate database(s) for query processing. You have access to two databases:

[1] PDK Database: Contains information about the process design kit, including standard cell libraries, library views, and operating conditions. This database is useful for questions about technology specifications, cell characteristics, and metal stack properties.
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
        * Overall cell area (as a single value, not dimensions)
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
        
[2] Design Database: Contains DEF information for a specific design (i.e cpu, multipler). It contains the following information:

- Design: Defines the design node including design name, die area, and physcial design stage (floorplan, placement, cts, routing).
- Pin: Defines input and output ports of the design, including pin names, direction, width, height, layer used for drawing the pin, pin signal type (whether it is a signal, power, or ground pin), and x,y location.
- Cell: Defines cells in the design including their area, including their name, height, width, area, power, whether cell is sequential, or physical only, or buffer, or inverter cell, and location.
- InternalCellPin: Defines information about the design cell pins including output pin transition, pin slack, pin rise arrival, pin fall arrival time, and input pin capacitances. 
- Net: Defines nets in the design including their name, capacitance, resistance, coupling, fanout, length, and net signal type (whether it is power, ground, or signal net).
- Segments: Defines metal layers used for routing the nets in the design like clock nets, specific signal nets, power and ground nets. 

For each user question:
1. Carefully analyze the content and intent of the question.
2. Determine which database(s) would be necessary to answer the question completely.
3. Provide a brief explanation for your choice, considering:
- The specific information required to answer the question
- Why the chosen database(s) is/are the most appropriate
- If both databases are needed, explain why the question can't be answered with just one
- Questions that requires computing design tradeoffs such as replacing cells with other types of cells, should be routed to both of them.
4. Output your decision in the following JSON format:

```json
{{
"explain": "<Your detailed explanation for the database choice>",
"pdk_db": "<'keep' if PDK database is needed, 'drop' if not>",
"design_db": "<'keep' if Design database is needed, 'drop' if not>"
}}

Here are some examples of user questions and their correponsding database:

User:  How many cells are in the high speed library in the PDK? 

Answer: 
{{
"explain": "The question only asks about information in the PDK so it should be routed to the PDK database only.",
"pdk_db": "keep",
"design_db": "drop"
}}

User:  How many cells are in the design? 

Answer: 
{{
"explain": "The question only asks about information in the design so it should be routed to the design database only.",
"pdk_db": "drop",
"design_db": "keep"
}}
"""

class DatabaseRouter(Agent):
    def __init__(self, model, temperature, few_shot=True, llm = None):
        super().__init__()
        system = DB_ROUTER_SYS_PROMPT
        self.prompt = ChatPromptTemplate.from_messages([
                ("system", str(system)),
                ("user", "{input}"),
            ]
        )

        if llm: 
            self.llm = llm 
        else: 
            self.llm = self.get_model(
                model=model,
                temperature=temperature,
                structured_output=False
            )
        
        self.router = self.prompt | self.llm 

    def route(self, query):
        out = self.router.invoke({"input": query})

        if type(out) != str: 
            out = out.content 

        print(out)
        out_parsed = parse_json_from_string(out)
        print(out_parsed)
        db = Database(**out_parsed)
        
        return db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/planner_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    args = parser.parse_args()
     
    model = args.model
    output = args.output 

    logger = get_logger(output)
    logger.info(f"CYAN: LLM Agent is {model}") 

    router = DatabaseRouter(
        model=model,
        temperature=0
    )

    pdk_acc = 0
    for query in test_queries: 
        logger.info(f"BLUE: User question is {query['input']}")
        out = router.route(query['input'])
        dbs = out.get_databases()
        score = dbs == ['pdk']
        pdk_acc += score
        color = 'GREEN' if score else 'RED'
        logger.info(f"{color}: Routed Database is {dbs}")
        logger.info(f"{color}: Explain: {out.explain}")

    pdk_acc = pdk_acc / len(test_queries)
    logger.info(f"YELLOW: PDK Accuracy is: {pdk_acc}")

    design_acc = 0
    for query in test_design: 
        logger.info(f"BLUE: User question is {query['input']}")
        out = router.route(query['input'])
        dbs = out.get_databases()
        score =  dbs == ['design']
        design_acc += score
        color = 'GREEN' if score else 'RED'
        logger.info(f"{color}: Routed Database is {dbs}")
        logger.info(f"{color}: Explain: {out.explain}")

    design_acc = design_acc / len(test_design)
    logger.info(f"YELLOW: Design Accuracy is: {design_acc}")
    
    design_pdk_acc = 0
    for query in test_design_pdk: 
        logger.info(f"BLUE: User question is {query['input']}")
        out = router.route(query['input'])
        dbs = out.get_databases()
        score = set(dbs) == set(['pdk', 'design'])
        design_pdk_acc += score
        color = 'GREEN' if score else 'RED'
        logger.info(f"{color}: Routed Database is {dbs}")
        logger.info(f"{color}: Explain: {out.explain}")

    design_pdk_acc = design_pdk_acc / len(test_design_pdk)
    logger.info(f"YELLOW: Design-PDK Accuracy is: {design_pdk_acc}")

            

if __name__ == '__main__':
    main()