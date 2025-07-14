"""
    Executes SQL/Cypher queries and refines errors in the generated Queries if needed
"""
import argparse

import sqlite3
import sqlalchemy
from langchain_core.prompts import ChatPromptTemplate
from neo4j.exceptions import CypherSyntaxError
from langchain_community.utilities import SQLDatabase
from langchain_community.graphs import Neo4jGraph
from neo4j.exceptions import ClientError, CypherSyntaxError, Neo4jError

from config.sky130 import cell_variant_sky130
from core.database.sql import get_desc, get_fk
from core.database.graphdb import get_node_descr, get_relationship_descr
from core.database.graphdb import URI, USER, PASSWORD
from core.agents.agent import Agent 
from core.graph_flow.states import DesignQueryState, PDKQueryState
from core.utils import parse_sql_from_string, get_logger, parse_cypher_from_string

from dotenv import load_dotenv
load_dotenv()


REFINER_SYS_PROMPT_SQL = """
When executing SQL below, some errors occurred, please fix up SQL based on the given [Query] and [Database schema] decription.
Solve the task step by step if you need to. Using SQL format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

[Constraints]
    - In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
    - In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
    - If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
    - If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
    - If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

[Requirements]
    1. You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to filter entries related to the operating condition and the standard cell variant the question is referring to. 
    2. Output the correct sql marked with ```sql```
 
[Query]
{input}
[Database schema]
{desc_str}
[Table Info]
{table_info}
[Foreign keys]
{fk_str}
[Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
[Old SQL]
```sql
{sql}
```
[SQLite error] 
{error}
[Exception class]
{exception_class}

Now please fixup old SQL and generate new SQL again.
[Correct SQL]
"""

REFINER_SYS_PROMPT_CYPHER = """
When executing Cypher below, some errors occurred, please fix up Cypher based on query and graph database info.
Solve the task step by step if you need to. Using Cypher format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

[Requirements]
- You must use the given stage [Stage] to query the correct design graph. 
 
[Query]
{input}
[Database Info]
{desc_str}
[Node Info]
{node_descr}
[Relationships]
{relationships}
[Stage]
{stage}
[Old Cypher]
```cypher
{cypher}
```
[Neo4j Error] 
{error}
[Exception class]
{exception_class}

Now please fixup old Cypher and generate new Cypher again.
[Correct Cypher]
"""

class RefinerSQL(Agent):
    def __init__(self, config) -> None:
        super().__init__()
        
        self.config = config

        system_sql = REFINER_SYS_PROMPT_SQL
        self.sql_prompt = ChatPromptTemplate.from_messages([
            ("system", str(system_sql)),
            ("user", ""),
        ])

        self.llm = config.lm_config.refiner_llm_model
        self.refiner_sql = self.sql_prompt | self.llm

    def refine(self, state: PDKQueryState):
        if self.config.flow_config.use_refiner: 
            question = state.get("question")
            fk_str = state.get("fk_str")
            descr_str = state.get("desc_str")
            error = state.get("error")
            table_info = state.get("table_info")
            scl_variant = state.get("scl_library")
            query = state.get("sql_query")
            refined_query = state.get("refined_query", query)
            exception_class = state.get("exception_class")
            refine_iters = state.get("refine_iters", 0)
            op_cond = state.get("op_cond")

            input_dict = {
                "input": question,
                "desc_str": descr_str,
                "error": error,
                "exception_class": exception_class,
                "sql": refined_query, 
                "fk_str": fk_str,
                "table_info": table_info,
                "scl_variant": scl_variant,
                "op_cond": op_cond,
            }
            
            if "deepseek-chat" in self.config.lm_config.refiner_lm_name: ## Hacky fix to unreliable API
                received = False
                while not received: 
                    try: 
                        stream = self.refiner_sql.stream(input_dict)
                        full = next(stream)
                        for chunk in stream:
                            full += chunk
                        full
                        received = True 
                    except ValueError as e:
                        print(f"[Reasoner]: Exception Happened Retrying... {e}")
                response = full
            else: 
                response = self.refiner_sql.invoke(input_dict)

            if type(response) != str: 
                response = response.content 
            
            refined_query = parse_sql_from_string(response)

            return {"refined_query": refined_query, "refine_iters": refine_iters+1} 
        else:
            query = state.get("sql_query")
            refine_iters = state.get("refine_iters", 0)
            return {"refined_query": query, "refine_iters": refine_iters+1}
         
    
    def execute(self, state: PDKQueryState):
        query = state.get("sql_query")
        view = state.get("view")
        scl_library = state.get("scl_library", [])
        pvt_corner = state.get("pvt_corner")
        techlef_corner = state.get("techlef_op_cond")
        refined_query = state.get("refined_query", query)
        
        try:
            database = self.config.db_config.get_database(
                view=view,
                scl_library=cell_variant_sky130(scl_library),
                pvt_corner=pvt_corner,
                techlef_corner=techlef_corner
            )
            result = database.run(refined_query)
        except (sqlalchemy.exc.OperationalError, sqlite3.OperationalError, 
                sqlite3.Warning, sqlalchemy.exc.ProgrammingError, ValueError) as error:
            exception_class = error.__class__.__name__
            return {
                "error": str(error), 
                "sql_executes": False, 
                "exception_class": exception_class, 
                "refined_query": refined_query,
                'result': str(error)
            } 

        return {"error": "", "sql_executes": True, "result": result, "refined_query": refined_query} 
     

class RefinerCypher(Agent):
    def __init__(self, config) -> None:
        super().__init__()
        
        self.config = config

        system_cypher = REFINER_SYS_PROMPT_CYPHER
        self.cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", str(system_cypher)),
            ("user", ""),
        ])
        

        self.llm = config.lm_config.refiner_llm_model
        self.refiner_cypher = self.cypher_prompt | self.llm

    def refine(self,  state: DesignQueryState):
        if self.config.flow_config.use_refiner: 
            question = state.get("question")
            stage = state.get("stage")
            error = state.get("error")
            node_descr = state.get("node_descr")
            edges = state.get("edges")
            query = state.get("cypher_query")
            refined_query = state.get("refined_query", query)
            exception_class = state.get("exception_class")
            refine_iters = state.get("refine_iters", 0)

            input_dict = {
                "input": question,
                "desc_str": node_descr,
                "error": error,
                "exception_class": exception_class,
                "cypher": refined_query,
                "node_descr": node_descr,
                "relationships": edges,
                "stage": stage,
            }
            
            response = self.refiner_cypher.invoke(input_dict)

            if type(response) != str: 
                response = response.content 
            
            refined_query = parse_cypher_from_string(response)

            return {"refined_query": refined_query, "refine_iters": refine_iters+1}
        else:
            query = state.get("cypher_query")
            refine_iters = state.get("refine_iters", 0)
            return {"refined_query": query, "refine_iters": refine_iters+1}
 
    
    def execute(self, state: DesignQueryState):
        query = state.get("cypher_query")
        refined_query = state.get("refined_query", query)

        try:
            result = self.config.db_config.design_database.query(refined_query)
        except (CypherSyntaxError, ClientError, Neo4jError, ValueError) as error: 
            exception_class = error.__class__.__name__,
            return {
                "error": str(error), 
                "cypher_executes": False, 
                "exception_class": exception_class, 
                "refined_query": refined_query,
                'result': str(error),
            } 

        if isinstance(result, dict) and 'error' in result:
            return {
                "error": str(result['error']), 
                "cypher_executes": False, 
                "refined_query": refined_query,
                'result': str(result['error']),
            } 
        
        return {
            "error": "", 
            "cypher_executes": True, 
            'refined_query': refined_query, 
            "refine_iters": 0, 
            "result": result
        }  


__all__ = [
  'RefinerSQL',
  'RefinerCypher'
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/refiner_eval.log')

    args = parser.parse_args()

    model = args.model
    output = args.output 
    
    logger = get_logger(output)
    logger.info(f"BLUE: LLM Agent: {model}") 

    
    refiner = RefinerSQL(
        model=model,
        temperature=0
    )

    # 1. Test with SQLite example
    database_path = "dbs/sky130.db"
    database = SQLDatabase.from_uri(
        f"sqlite:///{database_path}", 
        view_support = True
    )
    
    refiner_prompt = refiner.sql_prompt.format(
        input="List the vias available that have mcon layer.", 
        desc_str=get_desc('TechnologyLef', ['Vias', 'ViaLayers']), 
        table_info=database.get_table_info(table_names=['Vias','ViaLayers']), 
        fk_str=get_fk('TechnologyLef', ['Vias', 'ViaLayers']), 
        scl_variant="sky130_fd_sc_hd", 
        op_cond="nom",
        sql="SELECT ViaID, Name FROM Vias JOIN ViaLayers ON Vias.ViaID = ViaLayers.ViaID WHERE Layer = 'mcon'",
        error="",
        exception_class=""
    )

    logger.info(f"MAGENTA: Refiner Prompt: {refiner_prompt}") 

    response = refiner.execute(
        input="List the vias available that have mcon layer.", 
        model=model,
        query="SELECT ViaID, Name FROM Vias JOIN ViaLayers ON Vias.ViaID = ViaLayers.ViaID WHERE Layer = 'mcon'",
        database=database, 
        desc_str=get_desc('TechnologyLef', ['Vias', 'ViaLayers']), 
        fk_str=get_fk('TechnologyLef', ['Vias', 'ViaLayers']), 
        table_info=database.get_table_info(table_names=['Vias','ViaLayers']), 
        scl_variant="sky130_fd_sc_hd", 
        op_cond="nom",
    )
    
    sql_query = parse_sql_from_string(response)

    logger.info(f"CYAN: Refiner Response: {response}") 
    logger.info(f"CYAN: Refiner SQL: {sql_query}") 

    # 3. Test with Cypher example
    node_descr = get_node_descr()
    relationships = get_relationship_descr()

    graph_database = Neo4jGraph(
        url=URI, 
        username=USER, 
        password=PASSWORD, 
        enhanced_schema=True
    ) 
    
    refiner = RefinerCypher()
    response = refiner.execute(
        input="Count the total number of cells in the design.",
        query="MATCH (c:Cell) RETURN COUNT(p) AS cell_count",
        database=graph_database,
        desc_str="Graph database with design information.",
        stage="routing",
        use_cypher=True,
        node_descr=node_descr,
        relationships=relationships
    )

    cypher_query = parse_cypher_from_string(response)

    logger.info(f"CYAN: Refiner Response: {response}") 
    logger.info(f"CYAN: Refined Cypher: {cypher_query}") 



if __name__ == '__main__':
    main()