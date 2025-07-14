from typing_extensions import TypedDict
from typing import List, Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class PDKQueryState(TypedDict):
    question: str 
    view: str 
    techlef_op_cond: List[str]
    temp_corner: str 
    voltage_corner: str
    pvt_corner: str
    op_cond: str
    scl_library: str
    tables: List[str]
    table_info: str 
    desc_str: str
    fk_str: str
    qa_pairs: List[str]
    sql_query: str 
    sql_executes: bool 
    error: str 
    exception_class: str 
    refined_query: str
    refine_iters: int = 0
    result: str 
    final_answer: str 


class DesignQueryState(TypedDict):
    question: str 
    stage: List[str] 
    nodes: List[str]
    edges: str
    node_descr: str 
    qa_pairs: List[str]
    cypher_query: str 
    cypher_executes: bool
    error: str
    exception_class: str 
    refined_query: str
    refine_iters: int = 0
    result: str 


class ChipQueryState(TypedDict):
    question: str 
    final_answer: str 
    query: Annotated[List[str], operator.add]
    result: Annotated[List[str], operator.add]
    messages: Annotated[Sequence[BaseMessage], add_messages]

