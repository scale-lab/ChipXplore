
import sqlite3

from langchain_community.graphs import Neo4jGraph
from langchain_community.utilities import SQLDatabase

from config.sky130 import View
from core.agents.agent import Agent
from core.database.graphdb import URI, USER, PASSWORD
from config.sky130 import SCLVariants, sky130_scl_corners, Sky130TechLefCorner

class LMConfigs:

    def __init__(self, router_lm, selector_lm, generator_lm, refiner_lm, planner_lm, interpreter_lm, temperature=0, generator_temperature=0) -> None:
        
        llm_set = set()        
        llm_dict = dict()
        agent = Agent()

        if generator_temperature != temperature: 
            llm_set.update([
                router_lm,
                selector_lm,
                refiner_lm,
                planner_lm,
                interpreter_lm
            ])
        else: 
            llm_set.update([
                router_lm,
                selector_lm,
                generator_lm,
                refiner_lm,
                planner_lm,
                interpreter_lm
            ])
    

        self.router_lm_name = router_lm 
        self.selector_lm_name = selector_lm 
        self.generator_lm_name = generator_lm 
        self.refiner_lm_name = refiner_lm 
        self.planner_lm_name = planner_lm 
        self.interpreter_lm_name = interpreter_lm 
        self.refiner_lm_name = interpreter_lm 

        for llm in llm_set:
            llm_dict[llm] = agent.get_model(
                model = llm,
                temperature=temperature
            )

        if generator_temperature != temperature:
            self.generator_llm_model = agent.get_model(
                model = generator_lm,
                temperature=generator_temperature
            )
        else: 
            self.generator_llm_model = llm_dict[generator_lm] 

        self.router_llm_model = llm_dict[router_lm] 
        self.selector_llm_model = llm_dict[selector_lm]
        self.refiner_llm_model = llm_dict[refiner_lm]  
        self.planner_llm_model = llm_dict[planner_lm]  
        self.interpreter_llm_model = llm_dict[interpreter_lm]  

    def set_router_lm(self, lm):
        self.router_lm = lm  

    def set_selector_lm(self, lm):
        self.selector_lm = lm  

    def set_query_generator_lm(self, lm):
        self.generator_lm = lm 

    def set_refiner_lm(self, lm):
        self.refiner_lm = lm  

    def self_planner_lm(self, lm):
        self.planner_lm = lm


class FlowConfigs:

    def __init__(self, few_shot=True, generator_few_shot=True, secure=False, use_planner=True, use_router=True, use_selector=True, decompose_query=True, use_refiner=True, use_in_mem_db=True, max_refine_iters=3, graph_recursion_limit=6, add_table_info=False) -> None:
        self.few_shot = few_shot
        self.generator_few_shot = generator_few_shot
        self.use_in_mem_db = use_in_mem_db
        self.use_planner = use_planner 
        self.use_router = use_router 
        self.use_selector = use_selector 
        self.use_refiner = use_refiner
        self.decompose_query = decompose_query 
        self.max_refine_iters= max_refine_iters
        self.graph_recursion_limit = graph_recursion_limit 
        self.secure = secure   
        self.add_table_info = add_table_info
        
    def set_use_planner(self, value):
        self.use_planner = value 

    def set_use_router(self, value):
        self.use_router = value 

    def set_use_selector(self, value):
        self.use_selector = value 

    def set_decompose_query(self, value):
        self.decompose_query = value 
    
    def set_use_refiner(self, value):
        self.use_refiner = value


class DatabaseConfig:

    def __init__(self, pdk_database="dbs/sky130_index.db", design_database="sky130pico", partition=False, in_mem_db=True, load_graph_db=True) -> None:
        
        self.partition = partition
        db_conn = {}
        if partition:
            for variant in SCLVariants:
                variant_name = variant.value
                key_lef = f"{variant_name}_{View.Lef.value}"
                disk_connection = sqlite3.connect(f"dbs/sky130/{key_lef}.db")
                memory_lef_conn = sqlite3.connect(f"file:{key_lef}_memdb?mode=memory&cache=shared", uri=True, check_same_thread=False)
                disk_connection.backup(memory_lef_conn)

                db_conn[key_lef] = SQLDatabase.from_uri(
                    f"sqlite:///file:{key_lef}_memdb?mode=memory&cache=shared&uri=true",
                    view_support=True
                )

                for corner in Sky130TechLefCorner:
                    key_tlef = f"{variant_name}_{View.TechLef.value}_{corner.value}"
                    disk_connection = sqlite3.connect(f"dbs/sky130/{key_tlef}.db")
                    memory_tlef_conn = sqlite3.connect(f"file:{key_tlef}_memdb?mode=memory&cache=shared", uri=True, check_same_thread=False)
                    disk_connection.backup(memory_tlef_conn)
                    db_conn[key_tlef] = SQLDatabase.from_uri(
                        f"sqlite:///file:{key_tlef}_memdb?mode=memory&cache=shared&uri=true",
                        view_support=True
                    )
                for corner in sky130_scl_corners[variant]:
                    key_lib = f"{variant_name}_{View.Liberty.value}_{corner.value}"
                    disk_connection = sqlite3.connect(f"dbs/sky130/{key_lib}.db")
                    memory_lib_conn = sqlite3.connect(f"file:{key_lib}_memdb?mode=memory&cache=shared", uri=True, check_same_thread=False)
                    disk_connection.backup(memory_lib_conn)
                    db_conn[key_lib] = SQLDatabase.from_uri(
                        f"sqlite:///file:{key_lib}_memdb?mode=memory&cache=shared&uri=true",
                        view_support=True
                    )

                self.pdk_database = db_conn 
        else:
            if in_mem_db: 
                disk_connection = sqlite3.connect(pdk_database)
                memory_connection = sqlite3.connect("file:main_memdb?mode=memory&cache=shared", uri=True, check_same_thread=False)
                disk_connection.backup(memory_connection)
                db_conn["single"] = SQLDatabase.from_uri(
                    "sqlite:///file:main_memdb?mode=memory&cache=shared&uri=true",
                    view_support=True,
                )
                self.pdk_database = db_conn["single"] 

            else:
                self.pdk_database = SQLDatabase.from_uri(
                    f"sqlite:///{pdk_database}", 
                    view_support = True
                )

            self.pdk_database.run("PRAGMA cache_size = 25600;")
            self.pdk_database.run("PRAGMA page_size = 16384;")
        
        if load_graph_db: 
            self.design_database = Neo4jGraph(
                url=URI, 
                username=USER, 
                password=PASSWORD, 
                database=design_database,
                enhanced_schema=True
            ) 
            self.design_database.refresh_schema()
        else:
            self.design_database = None 
            
    def get_pdk_database(self):
        return self.pdk_database 
    
    def get_design_database(self):
        return self.design_database 
    
    def get_database(
        self, view: str, scl_library: list[str], pvt_corner: str, techlef_corner: list[str]
    ):
        if self.partition: 
            if view == View.Liberty.value:
                key = f"{scl_library[0]}_{view}_{pvt_corner}"
            elif view == View.TechLef.value:
                key = f"{scl_library[0]}_{view}_{techlef_corner[0]}"
            elif view == View.Lef.value:
                key = f"{scl_library[0]}_{view}"  

            return self.pdk_database[key] 
        else:
            return self.pdk_database


class ChipQueryConfig:

    def __init__(self, flow_config: FlowConfigs, lm_config: LMConfigs, db_config: DatabaseConfig) -> None:        
        self.flow_config = flow_config 
        self.lm_config = lm_config
        self.db_config = db_config 

    def set_flow_config(
        self, flow_config: FlowConfigs
    ):
        self.flow_config = flow_config 

    def set_llm_config(
        self, lm_config: LMConfigs
    ):
        self.lm_config = lm_config
