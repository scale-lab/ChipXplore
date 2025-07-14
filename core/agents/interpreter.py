import os
import argparse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.prompt_selector import ConditionalPromptSelector
from langchain_community.utilities import SQLDatabase
from termcolor import colored
from langchain_community.graphs import Neo4jGraph

from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.graph_flow.states import ChipQueryState, PDKQueryState
from core.eval.test_set import test_queries
from core.eval.test_graph import test_design 
from core.database.graphdb import URI, USER, PASSWORD
from core.agents.agent import Agent 
from config.config import ChipQueryConfig

from dotenv import load_dotenv
load_dotenv()


PROMPT = """Given the following user question and corresponding queries with their results, analyze the data and provide a comprehensive answer.

Question: {input}

{query_blocks}

Analyze all results and synthesize an accurate and insightful response.

Answer:
"""



class Interpreter(Agent):
    
    def __init__(self, config: ChipQueryConfig,  use_dual_db=False) -> None:
        super().__init__()
        self.config = config
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", str(PROMPT)),
                ("user", "{input}"),
            ]
        )
        self.llm = config.lm_config.interpreter_llm_model 
        self.interpreter = self.prompt | self.llm
        
        
    def interpret(self, state: ChipQueryState):
        question = state.get("question")
        queries = state.get("query")
        results = state.get("result")
        
        query_blocks = "\n\n".join([
            f"Query: {query}\n"
            f"Result: {result}"
            for query, result in zip(queries, results)
        ])
        
        if "deepseek-chat" in self.config.lm_config.interpreter_lm_name: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.interpreter.stream({
                        "input": question, 
                        'query_blocks': query_blocks
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
            out = self.interpreter.invoke({
                "input": question, 
                'query_blocks': query_blocks
            })
        
        if type(out) != str:
            out = out.content 
        
        return out
    
    def interpret_pdk(self, state: PDKQueryState):
        question = state.get("question")
        query = state.get("sql_query")
        result = state.get("result")
        
        query_blocks = "\n\n".join([
            f"Query: {query}\n"
            f"Result: {result}"
        ])
        
        out = self.interpreter.invoke({
            "input": question, 
            'query_blocks': query_blocks
        })
        
        if type(out) != str:
            out = out.content 
        
        return {"final_answer": out}
    

__all__ = [
  'Interpreter'
]



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/interpreter_eval.log')
    args = parser.parse_args()

    model = args.model 
    output = args.output 
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
            temperature=0,
        ),
        db_config=DatabaseConfig(
            partition=True,
            in_mem_db=True
        )
    )
    
    interpreter = Interpreter(
       config=config
    )

   
    state = {
        "question": "How many cells are in the high speed library ? ",
        "query": ["SELECT COUNT(*) FROM Cells"],
        "result": ["370"]
    }
    
    result = interpreter.interpret(
        state=state
    )

    print(colored(f"User Question is: {state['question']} \n", 'cyan'))   
    print(colored(f"Query is: {state['query'][0]} \n", 'magenta'))     
    print(colored(f"Result is: {state['result']} \n", 'green'))     
    print(colored(f"LLM Answer is:  {result}\n", 'yellow')) 


if __name__ == '__main__':
    main()