from openai import OpenAI
from langchain_core.tools import StructuredTool
from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities import SQLDatabase

from langchain_core.tools import tool
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.graph_flow.design_flow import DesignGraph
from core.graph_flow.pdk_flow import PDKGraph
from core.database.graphdb import URI, USER, PASSWORD
from PDQ.core.graph_flow.reasoner import _PDK_QUERY_DESCR, _DESIGN_QUERY_DESCR, _FINISH_DESCR


output = "./"
model = "gpt-3.5-turbo-0125"
temperature = 0
few_shot = True

config = ChipQueryConfig(
    flow_config= FlowConfigs(
        few_shot=few_shot,
        use_in_mem_db=True,
        graph_recursion_limit=10
    ),
    lm_config=LMConfigs(
        router_lm=model,
        selector_lm=model,
        generator_lm=model,
        refiner_lm=model,
        planner_lm=model,
        temperature=temperature
    ),
    db_config=DatabaseConfig(
        partition=True,
        in_mem_db=True
    )
)

pdk_subgraph = PDKGraph(
    config=config
)

design_subgraph = DesignGraph(
    config=config
)

@tool
def pdk_query(question: str):
    """
    Retrieves information from the PDK database such as information about standard cell libraries, library views, and operating conditions.
    """
    output = pdk_subgraph.forward(question)
    return output['result']

@tool
def design_query(question):
    """
    Retrieves information from the design database.
    """
    output = design_subgraph.forward(question)
    return output['result']


tools = [{
    "type": "function",
    "function": {
        "name": "pdk_query",
        "description": " Retrieves information from the PDK database such as information about standard cell libraries, library views, and operating conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "question to ask for the PDK database"
                },
            },
            "required": ["question"],
            "additionalProperties": False
        },
        "strict": True
    }
},

{
    "type": "function",
    "function": {
        "name": "design_query",
        "description": "Retrieves information from the design database.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "question to ask for the Design database"
                },
            },
            "required": ["question"],
            "additionalProperties": False
        },
        "strict": True
    }
}
]

client = OpenAI()

completion = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Can you find information about how many cells are in the high density library?"}],
    tools=tools
)

for c in completion: 
    print(c)
print(completion.choices[0].message.tool_calls)
