"""Cypher Chain
"""
import time 
import argparse
from langchain_community.graphs import Neo4jGraph

from core.utils import get_logger, parse_cypher_from_string, parse_qa_pairs
from core.agents.refiner import RefinerCypher
from core.agents.routers.router import StageRouter
from core.agents.interpreter import Interpreter 
from core.agents.generator.cypher_generator import CypherGenerator
from core.agents.selectors.node_selector import NodeSelector
from core.eval.test_graph import test_design 
from core.eval.metrics import compute_execution_acc, compute_ves
from core.eval.cases import design_cases
from core.database.graphdb import URI, USER, PASSWORD, get_node_descr, get_relationship_descr, get_relationship_descr_verbose

class CypherChain:
        
    def __init__(self, model, temperature=0, few_shot=True, use_router=True, use_selector=True, use_decomposer=True, use_refiner=True, use_interpreter=True, llm=None,  \
                 use_vanilla_rag=False, use_din_mac=False):
        
        self.use_router = use_router
        self.use_selector = use_selector 
        self.use_decomposer = use_decomposer
        self.use_refiner = use_refiner
        self.use_interpreter = use_interpreter 
        
        self.router = StageRouter(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        ) 
        self.selector = NodeSelector(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            llm=llm
        )
        self.cypher_generator = CypherGenerator(
            few_shot=few_shot,
            model=model,
            temperature=temperature,
            decompose=use_decomposer,
            use_vanilla_rag=use_vanilla_rag,
            use_din_mac=use_din_mac,
            llm=llm
        )
        self.refiner = RefinerCypher(
            model=model,
            temperature=temperature,
            llm=llm
        )
        self.interpreter = Interpreter(
            model=model,
            temperature=temperature,
            llm=llm
        ) 
        

    
    def generate(self, question, database, run_interpreter=False):
        # 1. Run Stage router
        if self.use_router: 
            stage = self.router.route(
                query=question
            )
            routed_stages = stage.get_stages()
        else:
            routed_stages = ['floorplan', 'placement', 'cts', 'routing']

        # 2. Run Node Selector 
        node_descr = get_node_descr()
        relationship = get_relationship_descr_verbose()
        
        if self.use_selector: 
            selected_nodes = self.selector.select(
                query=question, 
                node_descr=node_descr,
                edges=relationship
            )
            selected_nodes = selected_nodes.get_selected_nodes()
            node_descr = get_node_descr(selected_nodes)
            relationship = get_relationship_descr_verbose(selected_nodes)
        else:
            selected_nodes = None 

        # 2. Run cypher generator        
        response = self.cypher_generator.generate(
            question=question, 
            stage=str(routed_stages), 
            schema=node_descr, 
            relationship=relationship,
        )
        
        qa_pairs = parse_qa_pairs(response)
        cypher_query = parse_cypher_from_string(response)
        
        # 2. Run Refiner
        if self.use_refiner: 
            final_cypher = self.refiner.execute(
                input=question, 
                query=cypher_query, 
                database=database,
                desc_str=node_descr,
                use_cypher=True,
            )
        else:
            final_cypher = cypher_query

        # 3. Run Interpreter
        try: 
            query_result = database.query(final_cypher)
        except:
            query_result = None 

        answer= '' 
        if self.use_interpreter: 
            answer = self.interpreter.interpret(
                question=question, 
                query=final_cypher,
                query_result=query_result,
                dialect='Cypher',
            )
            
        steps = {
            'stage': routed_stages,
            'selected_nodes': selected_nodes,
            'cypher_query': cypher_query,
            'query_result': query_result,
            'refined_cypher': final_cypher, 
            'answer': answer,
            'qa_pairs': qa_pairs     
        }

        return steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/cypher_chain_eval.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--wo_fewshot', action='store_true', default=False)
    parser.add_argument('--wo_decomposer', action='store_true', default=False)
    parser.add_argument('--wo_selector', action='store_true', default=False)
    parser.add_argument('--wo_router', action='store_true', default=False)
    parser.add_argument('--wo_refiner', action='store_true', default=False)
    parser.add_argument('--wo_interpreter', action='store_true', default=False)
    parser.add_argument('--run_cases', action='store_true', default=False)
    args = parser.parse_args()
    
    output = args.output
    model = args.model 
    use_selector = not args.wo_selector
    few_shot = not args.wo_fewshot
    use_decomposer = not args.wo_decomposer 
    use_refiner = not args.wo_refiner
    use_selector = not args.wo_selector
    use_router = not args.wo_router
    use_interpreter = not args.wo_interpreter
    run_cases = args.run_cases 

    logger = get_logger(output)
    logger.info(f"CYAN: LLM Agent is {model}") 
    logger.info(f"CYAN: Few Shot Set to {few_shot}") 

    graph = Neo4jGraph(
        url=URI, 
        username=USER, 
        password=PASSWORD, 
        database='sky130',
        enhanced_schema=True
    ) 
    
    graph.refresh_schema()
    
    node_descr = get_node_descr()
    relationship = get_relationship_descr_verbose()
        
    cypher_chain = CypherChain(
        model=model,
        temperature=0,
        use_selector=use_selector,
        use_decomposer=use_decomposer,
        use_refiner=use_refiner,
        use_router=use_router,
        use_interpreter=use_interpreter
    )
    
    cypher_generator_prompt = cypher_chain.cypher_generator.prompt.format(
        question="How many cells are in the design ?", 
        stage="routing", 
        schema=node_descr, 
        relationship=relationship,
    )
    
    logger.info(f"MAGENTA: CypherGenerator Prompt: {cypher_generator_prompt}") 

    predicted_cyphers = []
    ground_truth_cyphers = []

    total_time = 0
    num_queries = len(test_design)
    
    test_set = design_cases if run_cases else test_design
    
    for query in test_set:         
        logger.info(f"CYAN: {query['input']}")

        start_time = time.time()
        steps = cypher_chain.generate(
            question=query["input"], 
            database=graph, 
            run_interpreter=True
        )

        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time
        
        refined_cypher = steps['refined_cypher']
        predicted_cyphers.append(refined_cypher)
        ground_truth_cyphers.append(query['ground_truth'])
                
        stage_score = cypher_chain.router.stage_metric(query['stage'], steps['stage']) 
        color = "GREEN" if stage_score else "RED"
        logger.info(f"{color}: Stage: {steps['stage']}")
        
        selector_score = cypher_chain.selector.compute_subset_accuracy(steps['selected_nodes'], query['selected_nodes']) 
        color = "GREEN" if selector_score else "RED"
        logger.info(f"{color}: Selected Nodes: {steps['selected_nodes']}")
        
        for pair in steps['qa_pairs']: 
            subquestion = pair[0]
            subquery = pair[1]
            logger.info(f"CYAN: Subquestion: {subquestion}")
            logger.info(f"Yellow: Subquery: {subquery}")
            
        ex = compute_execution_acc([refined_cypher], [query['ground_truth']], graph, use_cypher=True)
        color = "GREEN" if ex else "RED"
        logger.info(f"{color}: Final Cypher Query: {steps['cypher_query']}")
        logger.info(f"{color}: Refined Cypher Query: {steps['refined_cypher']}")
        logger.info(f"Yellow: LLM Answer: {steps['answer']}")

        break 

    num_iters = 5 
    ex = compute_execution_acc(predicted_cyphers, ground_truth_cyphers, graph, use_cypher=True)
    ves = compute_ves(predicted_cyphers, ground_truth_cyphers, graph, num_iters=num_iters, use_cypher=True)
    logger.info(f"WHITE: Overall Execution Accuracy {ex}, Overall Valid Efficiency Score {ves}")
    
    # average QA time
    average_time = total_time / num_queries
    logger.info(f"WHITE: Average time per query: {average_time:.2f} seconds")


if __name__ == '__main__':
    main()
    