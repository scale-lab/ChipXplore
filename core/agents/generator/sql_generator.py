
import argparse


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.example_selectors.base import BaseExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector

from config.sky130 import cell_variant_sky130
from core.utils import get_logger, parse_qa_pairs, parse_sql_from_string
from core.eval.test_set import test_queries, test_queries_tlef, test_queries_lib, test_queries_lef
from core.eval.metrics import compute_execution_acc, compute_ves
from core.agents.few_shot.sql import decomposer_few_shot 
from core.agents.few_shot.sql_partitioned import decomposer_few_shot_partition
from core.database.sql import get_desc, get_table_names, get_fk
from core.agents.selectors.table_selector import SchemaSelector
from core.agents.routers.router import Router
from core.agents.routers.view_router import View
from core.agents.refiner import RefinerSQL 
from core.agents.agent import Agent
from core.graph_flow.states import PDKQueryState
from core.agents.generator.prompt import *

from dotenv import load_dotenv
load_dotenv()


class CustomExampleSelector(BaseExampleSelector):
  """Few shot selector based on the routed library vew
  """
  def __init__(self, examples):
    self.examples = examples

  def add_example(self, example):
    self.examples.append(example)

  def select_examples(self, input_variables):
    input_view = input_variables["view"]

    best_match = []
    for example in self.examples:
        if example['source'] == input_view:
            best_match.append(example)
            
    return best_match



class Decomposer(Agent):
    
  def __init__(self, config, use_sql_coder_prompt=False) -> None:
    super().__init__()
    
    self.config = config

    if config.db_config.partition: 
      if config.flow_config.decompose_query: 
        system_prompt = DECOMPOSER_SYS_PROMPT('SQLite', REQS_PARTITION)
      else: 
        system_prompt = DECOMPOSER_WO_DECOMPOSE_SYS_PROMPT('SQLite', REQS_PARTITION)

    else:
      if config.flow_config.decompose_query: 
        system_prompt = DECOMPOSER_SYS_PROMPT('SQLite', REQS)
      else:
        system_prompt = DECOMPOSER_WO_DECOMPOSE_SYS_PROMPT('SQLite', REQS_PARTITION)

    if config.flow_config.decompose_query: 
      if config.db_config.partition: 
        EXAMPLE_PROPMT = DECOMPOSER_EXAMPLE_SUBQ_PARTITION
        SUFFIX_PROMPT = DECOMPOSER_SUFFIX_SUBQ_PARTITION
      else:
        EXAMPLE_PROPMT = DECOMPOSER_EXAMPLE_SUBQ
        SUFFIX_PROMPT = DECOMPOSER_SUFFIX_SUBQ
      
    else:
      if config.db_config.partition: 
        EXAMPLE_PROPMT = DECOMPOSER_EXAMPLE_ZSHOT_PARTITION
        SUFFIX_PROMPT = DECOMPOSER_SUFFIX_ZSHOT_PARTITION 
      else: 
        EXAMPLE_PROPMT = DECOMPOSER_EXAMPLE_ZSHOT
        SUFFIX_PROMPT = DECOMPOSER_SUFFIX_ZSHOT 

    
    if config.flow_config.generator_few_shot: 
      system_prompt += """Here are some examples for user questions and their corresponding query decomposition:"""        

      if config.db_config.partition: 
        example_selector = CustomExampleSelector(decomposer_few_shot_partition)
      else:
        example_selector = CustomExampleSelector(decomposer_few_shot)

      self.prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=PromptTemplate.from_template(EXAMPLE_PROPMT),
        input_variables=["input", "view", "desc_str", "fk_str", 'scl_variant', 'op_cond'],
        prefix=system_prompt,
        suffix=SUFFIX_PROMPT
      )
    else: 
      if use_sql_coder_prompt: 
        self.prompt = ChatPromptTemplate.from_messages(
        [
          ("system", str("")),
          ("user", SQL_CODER_USER_PROMPT),
        ]
      )
      else: 
        self.prompt = ChatPromptTemplate.from_messages(
          [
            ("system", str(system_prompt)),
            ("user", SUFFIX_PROMPT),
          ]
        )
    
    self.llm = config.lm_config.generator_llm_model
    self.generator = self.prompt | self.llm

      
  def decompose(self, state: PDKQueryState):
         
    query = state.get("question")
    view = state.get("view")
    desc_str = state.get("desc_str")

    if self.config.flow_config.add_table_info: 
      table_info = state.get("table_info")
    else: 
      table_info = ""
      
    fk_str = state.get("fk_str")
    scl_variant = cell_variant_sky130(state.get("scl_library"))

    if view == View.Liberty.value:
      op_cond = f"Temperature: {state.get('temp_corner')}, Voltage: {state.get('voltage_corner')}" 
    elif view == View.TechLef.value: 
      op_cond = state.get("techlef_op_cond")
    else: 
      op_cond = ""

    if "deepseek-chat" in self.config.lm_config.selector_lm_name: ## Hacky fix to unreliable API
      received = False
      while not received: 
        try: 
          stream = self.generator.stream({
            "input": query, 
            'view': view,
            'desc_str': desc_str,
            'table_info': table_info,
            'fk_str': fk_str,
            'scl_variant': scl_variant,
            'op_cond': op_cond
          })
          full = next(stream)
          for chunk in stream:
              full += chunk
          full
          received = True 
        except ValueError as e:
          print(f"[Reasoner]: Exception Happened Retrying... {e}")
      out = full 
    else: 
      out = self.generator.invoke({
        "input": query, 
        'view': view,
        'desc_str': desc_str,
        'table_info': table_info,
        'fk_str': fk_str,
        'scl_variant': scl_variant,
        'op_cond': op_cond
      })
    
    if type(out) != str:
      response = out.content 
    else:
      response = out   

    qa_pairs = parse_qa_pairs(response)
    final_sql = parse_sql_from_string(response)
    
    return {'qa_pairs': qa_pairs, 'sql_query': final_sql, "op_cond": op_cond}


__all__ = [
  'Decomposer'
]


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
  parser.add_argument('--wo_fewshot', action='store_true', default=False)
  parser.add_argument('--wo_decompose', action='store_true', default=False)
  parser.add_argument('--wo_selector', action='store_true', default=False)
  parser.add_argument('--use_router_selector', action='store_true', default=False)
  parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/decomposer_eval.log')
  
  args = parser.parse_args()
  
  model = args.model
  dialect = args.dialect
  output = args.output 
  use_router_selector = args.use_router_selector
  few_shot = not args.wo_fewshot 
  use_selector = not args.wo_selector
  decompose = not args.wo_decompose 

  logger = get_logger(output)
  logger.info(f"BLUE: LLM Agent: {model}") 
  logger.info(f"BLUE: SQL Dialect: {dialect}") 

  database = SQLDatabase.from_uri(
    f"sqlite:///dbs/sky130.db", 
    view_support = True
  )
    
  # Init LLM Agents 
  router = Router(
    model=model,
    temperature=0,
    few_shot=True
  ) 
  selector = SchemaSelector(
    model=model,
    temperature=0,
    few_shot=True
  ) 
  decomposer = Decomposer(
    model=model,
    temperature=0,
    few_shot=few_shot, 
    decompose=decompose,
    use_vanilla_prompt=False,
    use_din_mac_prompt=False
  )
  refiner = RefinerSQL(
    model=model,
    temperature=0
  )

  decomposer_prompt = decomposer.prompt.format(
    input="What is the area of the sky130_fd_sc_hd__nand2_1 cell ?",
    view="",
    desc_str= get_desc('Liberty', ['Cells', 'Operating_Conditions']),
    table_info=database.get_table_info(table_names=['Cells','Operating_Conditions']), 
    scl_variant="",
    op_cond="",
    fk_str = get_fk('Liberty', ['Cells', 'Operating_Conditions']),
  )
  
  logger.info(f"MAGENTA: Decomposer Prompt: {decomposer_prompt}") 

  sql_correct = 0
  sql_correct_byview = {'Liberty': 0, 'Lef': 0, 'TechnologyLef': 0}
  
  for query in test_queries_lib:
    logger.info(f"BLUE: User Question: {query['input']}")

    if use_router_selector: 
      routed_scl_variant, routed_view, query_op_cond = router.route(query=query["input"], model=model, temperature=0)
      query_view = routed_view.datasource

      table_names = get_table_names(query_view)
      
      selected_tables = selector.select(
        query=query['input'], 
        datasource=query_view, 
        desc_str=get_desc(query_view), 
        fk_str=get_fk(query_view), 
        table_info=database.get_table_info(table_names=table_names), 
        model=model
      )
      
      query_tables = selected_tables.get_selected_columns() 
      query_scl = cell_variant_sky130(routed_scl_variant) 
      
    else: 
      query_tables = query["selected_tables"]  
      query_view = query['view']
      query_scl = cell_variant_sky130(query['scl_variant'])
      query_op_cond = f"Operating Corners: {query['op_cond']}"

    query_tables_descr = get_desc(query_view, query_tables)
    fk_str = get_fk(query_view, query_tables)
    table_info = database.get_table_info(table_names=query_tables)

    logger.info(f"YELLOW: Routed View: {query_view}")
    logger.info(f"YELLOW: Routed Cell Library: {query_scl}")
    logger.info(f"YELLOW: Routed Operating Conditions: {query_op_cond}")
    logger.info(f"YELLOW: Selected Tables: {query_tables}")
    logger.info(f"BLUE: Table Descriptions: {query_tables_descr}")
    logger.info(f"BLUE: Foreign Keys: {fk_str}")
          
    # 3. Run Decomposer      
    response = decomposer.decompose(
      query=query['input'],
      view=query['view'],
      desc_str=query_tables_descr,
      table_info=table_info, 
      fk_str=fk_str,
      scl_variant=query_scl,
      op_cond=query_op_cond
    )

    logger.info(f"MAGENTA: Decomposer Response: {response}")
  
    qa_pairs = parse_qa_pairs(response)
    final_sql = parse_sql_from_string(response)

    for pair in qa_pairs: 
      subquestion = pair[0]
      subquery = pair[1]
      logger.info(f"CYAN: Subquestion: {subquestion}")
      logger.info(f"Yellow: Subquery: {subquery}")
      
    logger.info(f"CYAN: Final SQL is: {final_sql}")
    
    # 4. Run Refiner to make sure SQL is executable 
    refiner_response = refiner.execute(
      input=query['input'],
      database=database,
      query=final_sql,
      desc_str=query_tables_descr,
      table_info=table_info,
      fk_str=fk_str,
      scl_variant=query_scl,
      op_cond=query_op_cond,
    )
    
    logger.info(f"MAGENTA: Refiner Response: {refiner_response}")
    
    refined_sql = parse_sql_from_string(refiner_response)
    logger.info(f"BLUE: Refined SQL is: {refined_sql}")
    
    
    acc = compute_execution_acc([refined_sql], [query['ground_truth']], database) 
    sql_correct += acc 
    sql_correct_byview[query_view]+= acc
    
    logger.info(f"BLUE: User Questions: \n {query['input']}")
    color = "GREEN: " if acc else "RED: "
    logger.info(f"{color} \n Predicted SQL: \n {refined_sql} \n Ground Truth SQL: \n {query['ground_truth']}")
    logger.info(f"{color} \n Accuracy is {acc}")

    
  decomposer_accuracy = sql_correct / len(test_queries)
  logger.info(f"BLUE: Decomposer accuracy is {decomposer_accuracy}")
  logger.info(f"BLUE: Decomposer accuracy TechLef is {sql_correct_byview['TechnologyLef'] / len(test_queries_tlef)}")
  logger.info(f"BLUE: Decomposer accuracy LEF is {sql_correct_byview['Lef'] / len(test_queries_lef)}")
  logger.info(f"BLUE: Decomposer accuracy Lib is {sql_correct_byview['Liberty'] / len(test_queries_lib)}")

      
  
if __name__ == '__main__':
  main()