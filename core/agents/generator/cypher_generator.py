"""Cypher Agent for chatting with design schema
"""
import os
import argparse 
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import (
    FewShotPromptTemplate,
    PromptTemplate,
)
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from core.database.graphdb import URI, USER, PASSWORD, get_node_descr, get_relationship_descr
from core.agents.refiner import RefinerCypher
from core.agents.agent import Agent
from core.agents.few_shot.cypher import cypher_generator_few_shot
from core.agents.selectors.node_selector import NodeSelector
from core.graph_flow.states import DesignQueryState
from core.eval.test_graph import test_design 
from core.eval.metrics import compute_execution_acc, compute_ves
from core.utils import get_logger, parse_qa_pairs, parse_cypher_from_string
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig

from dotenv import load_dotenv
load_dotenv()


CYPHER_SYS_PROMPT = """Given a [Schema] description, and a [Question], you need to use valid Cypher and understand the schema, and then decompose the question into subquestions for text-to-Cypher generation.
[Instructions]
- Use only the provided relationship types and properties in the schema.
- Do not use any other relationship types or properties that are not provided.
- Do not include any explanations or apologies in your responses.
- Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
- Do not include any text except the generated Cypher statement.
- Use the specified [Stage] to query the correct design graph. 
""" 


CYPHER_EXAMPLE_PROMPT_ZSHOT =  """[Question]
{question}
[Stage]
{stage}

Generate final Cypher, considering [Stage].Give your answer in the same format as the given example:
{query}
"""


CYPHER_EXAMPLE_PROMPT_SUBQ = """
[Question]
{question}
[Stage]
{stage}

Decompose the question into sub questions, considering [Stage], and generate the Cypher after thinking step by step:
{decompose_str}
"""


CYPHER_EXAMPLE_SUFFIX_ZSHOT = """[Question]
{question}
[Stage]
{stage}

Generate final Cypher, considering [Stage].Give your answer in the same format as the given example:
"""


CYPHER_EXAMPLE_SUFFIX_SUBQ = """[Question]
{question}
[Stage]
{stage}

Decompose the question into sub questions, considering [Stage], and generate the Cypher after thinking step by step. Give your answer in the same format as the given example:
"""



class CypherGenerator(Agent):
    
    def __init__(self, config, use_vanilla_rag=False, use_din_mac=False):
        super().__init__()
        self.config = config
        if config.flow_config.decompose_query: 
            EXAMPLE_PROMPT = CYPHER_EXAMPLE_PROMPT_SUBQ
            SUFFIX_PROMPT = CYPHER_EXAMPLE_SUFFIX_SUBQ
        else:
            EXAMPLE_PROMPT = CYPHER_EXAMPLE_PROMPT_ZSHOT
            SUFFIX_PROMPT = CYPHER_EXAMPLE_SUFFIX_ZSHOT

        self.system_prompt = CYPHER_SYS_PROMPT
    
        self.system_prompt += """
[Schema] The database contains a snapshot of the design at different stages: floorplan, placement, cts, and routing. 
{schema}
[Relationships]
{relationship}
"""
        if config.flow_config.few_shot: 
            self.system_prompt += """Here are some examples for user questions and their corresponding query:"""        
            example_selector = SemanticSimilarityExampleSelector.from_examples(
                cypher_generator_few_shot,  
                OpenAIEmbeddings(),
                FAISS,
                k=3,           
            )
            self.prompt = FewShotPromptTemplate(
                example_selector=example_selector,
                example_prompt=PromptTemplate.from_template(EXAMPLE_PROMPT), 
                input_variables=["stage", "question", "query"], 
                prefix=self.system_prompt,
                suffix=SUFFIX_PROMPT
            )
        else: 
            self.prompt = PromptTemplate(
                input_variables=["stage", "question"], 
                template=self.system_prompt
            )

        self.llm = config.lm_config.generator_llm_model
    
        self.generator = self.prompt | self.llm 

    def generate(self, state: DesignQueryState):       
        
        question = state.get("question")
        stage = str(state.get("stage"))
        node_descr = state.get("node_descr")
        relationship = state.get("edges")

        if "deepseek-chat" in self.config.lm_config.generator_lm_name: ## Hacky fix to unreliable API
            received = False
            while not received: 
                try: 
                    stream = self.generator.stream({
                        'question': question, 
                        'schema': node_descr,
                        'relationship': relationship,
                        'stage': stage
                    })
                    
                    full = next(stream)
                    for chunk in stream:
                        full += chunk
                    full
                    received = True 
                except ValueError as e:
                    print(f"[Cypher-Generator] Exception Happened Retrying... {e}")
            output = full 
        else: 
            output = self.generator.invoke({
                'question': question, 
                'schema': node_descr,
                'relationship': relationship,
                'stage': stage
            })

        if type(output) != str:
            response = output.content 
        else:
            response = output   
            
        qa_pairs = parse_qa_pairs(
            text=response
        )
        cypher_query = parse_cypher_from_string(
            input_string=response
        )
        

        return {"qa_pairs": qa_pairs, "cypher_query": cypher_query}
    
    
__all__ = [
  'CypherChain'
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--wo_selector', action='store_true', default=False)
    parser.add_argument('--wo_decomposition', action='store_true', default=False)
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/graphqa.log')
    
    args = parser.parse_args()
    
    model = args.model 
    output = args.output 
    fewshot = not args.wo_fewshot 
    use_selector = not args.wo_selector 
    decompose = not args.wo_decomposition 
    
    logger = get_logger(output)
    logger.info(f"BLUE: LLM Agent: {model}") 

    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=True,
            use_planner=True,
            use_router=True,
            use_selector=True,
            decompose_query=True,
            use_refiner=True,
            use_in_mem_db=True,
            graph_recursion_limit=10
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=model,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=model,
        ),
        db_config=DatabaseConfig(
            partition=True,
            in_mem_db=True
        ),
    )

    node_descr = get_node_descr()
    relationship = get_relationship_descr()
        
    cypher_generator = CypherGenerator(
       config=config
    )

    node_selector = NodeSelector(
       config=config
    )
    
    refiner = RefinerCypher(
        config=config
    )
    
    cypher_generator_prompt = cypher_generator.prompt.format(
        question="What is the average pin slack in the design?", 
        stage="placement", 
        schema=node_descr, 
        relationship=relationship
    )
    logger.info(f"MAGENTA: CypherGenerator Prompt: {cypher_generator_prompt}") 
    
    predicted_cyphers = []
    ground_truth_cyphers = []
    
    for query in test_design: 
        logger.info(f"CYAN: {query['input']}")
        
        if use_selector:
            output = node_selector.select({
                "question": query["input"],
            })
            selected_nodes = output["nodes"]
            
        else:
            selected_nodes = query['selected_nodes']
        
        exact_score = node_selector.compute_exact_accuracy(
            selected_nodes, 
            query["selected_nodes"]
        )
        relaxed_score = node_selector.compute_subset_accuracy(
            selected_nodes, 
            query["selected_nodes"]
        )

        color = 'GREEN' if relaxed_score else 'RED'
        logger.info(f"{color}: Selected Nodes are {selected_nodes}")

        node_descr = get_node_descr(selected_nodes)
        relationship = get_relationship_descr(selected_nodes)
                
        response = cypher_generator.generate({
            "question": query["input"], 
            "stage": str(query['stage']), 
            "node_descr": node_descr, 
            "edges": relationship,
        })
        
        qa_pairs = response["qa_pairs"]
        cypher_query = response["cypher_query"]
        
        for pair in qa_pairs: 
            subquestion = pair[0]
            subquery = pair[1]
            logger.info(f"CYAN: Subquestion: {subquestion}")
            logger.info(f"Yellow: Subquery: {subquery}")
            
        logger.info(f"CYAN: Final Cypher Query is: {cypher_query}")
        
        refiner_output = refiner.execute({
            "question": query['input'],
            "cypher_query": cypher_query,
            "node_descr": node_descr
        })

        refined_cypher = refiner_output["refined_query"]
        
        logger.info(f"BLUE: Refined Cypher Query: {refined_cypher}")
        
        predicted_cyphers.append(refined_cypher)
        ground_truth_cyphers.append(query['ground_truth'])

        ex = compute_execution_acc(
            predicted_queries=[refined_cypher], 
            ground_truth_queries=[query['ground_truth']], 
            database=config.db_config.design_database, 
            use_cypher=True
        )

        color = "GREEN" if ex else "RED"
        logger.info(f"{color}: Cypher Query: {cypher_query}")
        logger.info(f"{color}: Refined Cypher Query: {refined_cypher}")
        logger.info(f"{color}: Accuracy is : {ex}")

    num_iters = 5 
    ex = compute_execution_acc(
        predicted_queries=predicted_cyphers, 
        ground_truth_queries=ground_truth_cyphers, 
        database=config.db_config.design_database, 
        use_cypher=True
    )
    ves = compute_ves(
        predicted_queries=predicted_cyphers, 
        ground_truth=ground_truth_cyphers,
        database=config.db_config.design_database, 
        num_iters=num_iters, 
        use_cypher=True
    )
    logger.info(f"WHITE: Overall Execution Accuracy {ex}, Overall Valid Efficiency Score {ves}")
    

if __name__ == '__main__':
    main()