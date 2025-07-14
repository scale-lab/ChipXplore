"""Main entry point for the framework
"""
import httpx
import json
import argparse

import langgraph 
import langsmith
from langsmith import Client
from langsmith import evaluate
from httpcore import RemoteProtocolError
from langchain.globals import set_debug, set_verbose

from core.utils import get_logger
from config.config import ChipQueryConfig, FlowConfigs, LMConfigs, DatabaseConfig
from core.agents.agent import Agent
from core.eval.test_graph import test_design
from core.eval.test_set import test_queries, test_queries_lef, test_queries_lib, test_queries_tlef, test_queries_byview
from core.eval.test_design_pdk import test_design_pdk
from core.eval.cases import pdk_cases, design_cases, pdk_design_cases
from core.eval.metrics import compute_execution_acc, compute_ves
from core.graph_flow.all_flow import ReActPlanner
from core.eval.interwined_questions import test_queries_interwined


# set_debug(True)
# set_verbose(True)

config = None 

class ChipQueryRunner(Agent):
    
    def __init__(self, config: ChipQueryConfig) -> None:
        super().__init__()
        self.planner = ReActPlanner(
            config=config
        )
        
    def forward(self, question):
        try: 
            output = self.planner.forward(
                question=question
            )
        except langgraph.errors.GraphRecursionError:
            return {
                'messages': [],
                'final_answer': "",
                'query': []
            }
        except json.JSONDecodeError: 
            self.forward(question=question) # call the function again until it works
        except RemoteProtocolError:
            self.forward(question=question) # call the function again until it works
        # except:
        #     return {
        #         'messages': [],
        #         'final_answer': "",
        #         'query': []
        #     }
        
        return output



def compute_accuracy(run, example) -> dict:
    global config 
    predicted_query = run.outputs.get("query")
    ground_truth_query = example.outputs.get("query")
    
    execution_accuracy = compute_execution_acc(
        predicted_queries=predicted_query, 
        ground_truth_queries=[ground_truth_query],
        database=config.db_config.pdk_database
    )

    valid_efficiency_score = compute_ves(
        predicted_queries=predicted_query,
        ground_truth=[ground_truth_query],
        database=config.db_config.pdk_database,
        num_iters=3
    )

    return {
        "results": [
            {"key": "execution_accuracy", "score": execution_accuracy},
            {"key": "valid_efficiency_score", "score": valid_efficiency_score}
        ]
    }


def compute_accuracy_cypher(run, example) -> dict:
    global config 
    predicted_query = run.outputs.get("query")
    ground_truth_query = example.outputs.get("query")
    
    execution_accuracy = compute_execution_acc(
        predicted_queries=predicted_query, 
        ground_truth_queries=[ground_truth_query],
        database=config.db_config.design_database,
        use_cypher=True
    )

    valid_efficiency_score = compute_ves(
        predicted_queries=predicted_query,
        ground_truth=[ground_truth_query],
        database=config.db_config.design_database,
        num_iters=3,
        use_cypher=True
    )

    return {
        "results": [
            {"key": "execution_accuracy", "score": execution_accuracy},
            {"key": "valid_efficiency_score", "score": valid_efficiency_score}
        ]
    }


def evaluate_length(run, example) -> dict:
    predicted_query = run.outputs.get("query") 
    _ = example.outputs.get("query")
    score = len(predicted_query)
    return {"key": "query_length", "score": score}


def create_QA(client, pdk_dataset_name, design_dataset_name, interwined_dataset_name, test_set_pdk, test_set_design, test_set_interwined, filter):
    pdk_dataset = dict()
    for key in pdk_dataset_name.keys():
        try: 
                pdk_dataset[key] = client.create_dataset(
                    dataset_name=pdk_dataset_name[key],
                    description=f"Question-to-SQL pairs for PDK-{key}.",
                )
        except langsmith.utils.LangSmithConflictError:
            pdk_dataset[key]= next(client.list_datasets(dataset_name=pdk_dataset_name[key]))

    try: 
        design_dataset = client.create_dataset(
            dataset_name=design_dataset_name,
            description="Question-to-SQL pairs for Design.",
        )
    except langsmith.utils.LangSmithConflictError:
        design_dataset = next(client.list_datasets(dataset_name=design_dataset_name))

    try: 
        interwined_dataset = client.create_dataset(
            dataset_name=interwined_dataset_name,
            description="Question-to-SQL pairs for both PDK & Desgin.",
        )
    except langsmith.utils.LangSmithConflictError:
        interwined_dataset = next(client.list_datasets(dataset_name=interwined_dataset_name))


    all_examples = list(client.list_examples(dataset_name=pdk_dataset_name["lef"])) + \
                    list(client.list_examples(dataset_name=pdk_dataset_name["tlef"])) + \
                    list(client.list_examples(dataset_name=pdk_dataset_name["lib"])) + \
                   list(client.list_examples(dataset_name=design_dataset_name)) + \
                   list(client.list_examples(dataset_name=interwined_dataset_name))
    
    for example in all_examples:
        client.delete_example(example_id=example.id)
    
    
    for key in pdk_dataset.keys(): 
        client.create_examples(
            inputs=[{"question": q["input"], 'view': q['view']} for q in test_set_pdk[key]],
            outputs=[{"query": q["ground_truth"]} for q in test_set_pdk[key]],
            dataset_id=pdk_dataset[key].id,
        )
    
    client.create_examples(
        inputs=[{"question": q["input"], 'stage': q['stage']} for q in test_set_design],
        outputs=[{"query": q["ground_truth"]} for q in test_set_design],
        dataset_id=design_dataset.id,
    )

    client.create_examples(
        inputs=[{"question": q["input"]} for q in test_set_interwined],
        outputs=[{"sql_query": q["sql_query"], "cypher_query": q["cypher_query"]} for q in test_set_interwined],
        dataset_id=interwined_dataset.id,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help='Path to output file for storing the output of each query', default='./output/runner.log')
    parser.add_argument('--model', type=str, help='Model name', default='gpt-3.5-turbo-0125')
    parser.add_argument('--generator', type=str, help='Model name', default=None)
    parser.add_argument('--wo_planner',  help='Run without planner agent, use one-shot', action='store_true', default=False)
    parser.add_argument('--wo_router',  help='Run without router agent', action='store_true', default=False)
    parser.add_argument('--wo_selector',  help='Run without selector agent', action='store_true', default=False)
    parser.add_argument('--wo_decomposer',  help='Run without query decomposition', action='store_true', default=False)
    parser.add_argument('--wo_refiner',  help='Run without refiner', action='store_true', default=False)
    parser.add_argument('--wo_interpreter',  help='Run without interpreter', action='store_true', default=False)
    parser.add_argument('--use_in_mem_db',  help='Run without interpreter', action='store_true', default=True)
    parser.add_argument('--filter', type=str, help='Filter examples to run by view, (lib, lef, tlef)', default='')
    parser.add_argument('--exp_name', type=str, help='experiment name', default='')
    parser.add_argument('--partition', help="partition database", action='store_true', default=False)
    parser.add_argument('--secure', help="Enable secure framework", action='store_true', default=False)

    args = parser.parse_args() 

    model = args.model
    generator = args.generator
    output = args.output 
    use_planner = not args.wo_planner 
    use_router = not args.wo_router 
    use_selector = not args.wo_selector
    decompose_query = not args.wo_decomposer 
    use_refiner = not args.wo_refiner 
    use_in_mem_db = args.use_in_mem_db
    partition = args.partition
    secure = args.secure
    filter = args.filter 
    exp_name = args.exp_name 

    if "gpt" in model and secure: 
        interpreter_lm = "llama3.3:70b"
    else:
        interpreter_lm = model 

    if generator is None: 
        generator = model 
    
    few_shot = True
    generator_temperature = 0
    generator_few_shot = few_shot 
    add_table_info = True 
    if "chipxplore" in generator: 
        decompose_query = False 
        generator_few_shot = False 
        generator_temperature = 0.1 
        add_table_info=False 

    global config 
    config = ChipQueryConfig(
        flow_config= FlowConfigs(
            few_shot=few_shot,
            generator_few_shot=generator_few_shot,
            secure=secure,
            use_planner=use_planner,
            use_router=use_router,
            use_selector=use_selector,
            decompose_query=decompose_query,
            use_refiner=use_refiner,
            use_in_mem_db=use_in_mem_db,
            graph_recursion_limit=15,
            add_table_info=add_table_info
        ),
        lm_config=LMConfigs(
            router_lm=model,
            selector_lm=model,
            generator_lm=generator,
            refiner_lm=model,
            planner_lm=model,
            interpreter_lm=interpreter_lm,
            generator_temperature=generator_temperature,
        ),
        db_config=DatabaseConfig(
            partition=partition,
            in_mem_db=True,
            load_graph_db=True
        ),
    )

    runner = ChipQueryRunner(
        config=config,
    )

    logger = get_logger(output)
    logger.info(f"CYAN: LLM Agent is {model}") 
    logger.info(f"CYAN: Use Router {use_router}, \
                Use Selector {use_selector}, \
                Use Decomposer {decompose_query}, \
                Use Refiner {use_refiner}.") 

    client = Client()

    pdk_dataset_name = {
        'lef': "PDK-LEF-QA-Chip-Query",
        "tlef": "PDK-TechLEF-QA-Chip-Query",
        "lib": "PDK-LIB-QA-Chip-Query",
    }
    design_dataset_name = "Design-QA-Chip-Query"
    interwined_dataset_name = "Interwined-QA-Chip-Query"

    create_QA(
        client=client, 
        pdk_dataset_name=pdk_dataset_name,
        design_dataset_name=design_dataset_name,
        interwined_dataset_name=interwined_dataset_name,
        test_set_pdk=test_queries_byview, 
        test_set_design=test_design, 
        test_set_interwined=test_queries_interwined,
        filter=filter
    )

    def answer(input):
        logger.info(f"BLUE: User question is {input['question']}")
        output = runner.forward(
            question=input['question']
        )
        logger.info(f"YELLOW: ***LLM Output is***: \n {output['final_answer']}, {output}")
        return output
    
    if exp_name:
        experiment_name = exp_name 
    else: 
        experiment_name = "ChipQuery"

    for key in ["tlef", "lef", "lib"]: 
        pdk_qa_results = evaluate(
            answer, 
            data=pdk_dataset_name[key],
            experiment_prefix=f"{experiment_name}-{key}-{model}",
            evaluators=[compute_accuracy, evaluate_length],
            max_concurrency=1
        )
        
        pdk_qa_results.wait()

        ex = pdk_qa_results._results[0]['evaluation_results']['results'][0].score
        ves = pdk_qa_results._results[0]['evaluation_results']['results'][1].score
        
        logger.info(f"YELLOW: Execution Accuracy (PDK-{key}), {ex}, Valid Efficiency Score (PDK-{key}), {ves}")

    if 'def' in filter or filter == '': 
        design_qa_results = evaluate(
            answer, 
            data=design_dataset_name,
            experiment_prefix=f"{experiment_name}_{design_dataset_name}-{model}",
            evaluators=[compute_accuracy_cypher, evaluate_length],
            max_concurrency=1
        )
        design_qa_results.wait()
        
        ex = design_qa_results._results[0]['evaluation_results']['results'][0].score
        ves = design_qa_results._results[0]['evaluation_results']['results'][1].score

        logger.info(f"YELLOW: Execution Accuracy (DEF), {ex}, Valid Efficiency Score (DEF), {ves}")

    # interwined_qa_results = evaluate(
    #     answer, 
    #     data=interwined_dataset_name,
    #     experiment_prefix=f"{interwined_dataset_name}-{model}",
    #     evaluators=[compute_accuracy_cypher, evaluate_length],
    #     max_concurrency=1
    # )
    # ex = interwined_qa_results._results[0]['evaluation_results']['results'][0].score
    # ves = interwined_qa_results._results[0]['evaluation_results']['results'][1].score

    # logger.info(f"YELLOW: Execution Accuracy (Interwined), {ex}, Valid Efficiency Score (Interwined), {ves}")


    # output = runner.forward(
    #     question="Which cell library has the smallest width for the mux4_1 cell ?"
    # )

    # for m in output['messages']:
    #     m.pretty_print()
    
    # logger.info(f"GREEN: Final Answer >> {output['final_answer']}")


    # output = runner.forward(
    #     question="What is the height of the and2_1 cell in the high speed library ?"
    # )
    
    # for m in output['messages']:
    #     m.pretty_print()
    
    # logger.info(f"GREEN: Final Answer >> {output['final_answer']}")

    # output = runner.forward(
    #     question="How many cells are in the design ? "
    # )

    # for m in output['messages']:
    #     m.pretty_print()
    
    # logger.info(f"GREEN: Final Answer >> {output['final_answer']}")


if __name__ == '__main__':
    main()