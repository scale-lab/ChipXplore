"""
Measure Run-time and token count of opendb scripts
"""

import re 
import os 
import glob 
import tqdm
import time 
import argparse 

import tiktoken
from langchain_community.graphs import Neo4jGraph

from core.utils import get_logger
from core.parsers.design.run import run_openroad_command
from core.eval.test_graph import test_design
from core.eval.metrics import execute_query 
from core.database.graphdb import URI, USER, PASSWORD

def measure_token_count(
    string,
    model="gpt-3.5-turbo-0125"
):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    
    # Remove comments
    code_no_comments = re.sub(r"#.*", "", string)
    code_cleaned = re.sub(r"\s+", " ", code_no_comments).strip()
    num_tokens_wo_comments = len(encoding.encode(code_cleaned))

    return num_tokens, num_tokens_wo_comments


def measure_runtime(
    script,
    odb_file,
    liberty_file,
    python=True
):
    args = argparse.Namespace(
        odb_file=odb_file,
    )
    start_time = time.time()
    result = run_openroad_command(
        script_path=script,
        args=args,
        python=python
    )
    run_time = time.time() - start_time 

    return run_time


def main():
    parser = argparse.ArgumentParser(description="Parse design files and output JSON")
    parser.add_argument('--input', type=str, help='Path to design files', default='./designs/spm-small')
    parser.add_argument('--stage', type=str, help='Specify specific stage', default='routing')
    parser.add_argument('--pdk', type=str, help='Path to PDK', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument("--output_dir", help="Output directory", default='./output')
    args = parser.parse_args() 
    
    stage = args.stage 
    input_dir = args.input 
    pdk_path = args.pdk 
    output_dir = args.output_dir 

    scl_variant = 'sky130_fd_sc_hd'
    lib_path = os.path.join(pdk_path, scl_variant, 'lib')
    techlef_path = os.path.join(pdk_path, scl_variant, 'techlef')
    lef_path = os.path.join(pdk_path, scl_variant, 'lef')

    logger = get_logger('opendb.log')

    liberty_files = [os.path.join(lib_path, file) for file in os.listdir(lib_path) if 'tt_025C_1v80' in file ]
    
    odb_file = glob.glob(os.path.join(input_dir, stage, '*.odb'))[0]
    python_scripts = glob.glob(os.path.join('baselines/opendb', 'python', '*.py'))
    tcl_scripts = glob.glob(os.path.join('baselines/opendb', 'tcl', '*.tcl'))

    graph_database = Neo4jGraph(
        database='sky130',
        url=URI, 
        username=USER, 
        password=PASSWORD, 
        enhanced_schema=True
    ) 


    total_run_time = 0
    total_token_count = 0
    total_token_count_wo_comments = 0

    for script in tqdm.tqdm(python_scripts):
        with open(script) as file:
            string = file.read()

        token_count, token_count_wo_comments = measure_token_count(
           string=string,
           model="gpt-3.5-turbo-0125"
        )

        run_time = measure_runtime(
            script=script, 
            odb_file=odb_file, 
            liberty_file=liberty_files,
            python=True
        )

        total_run_time += run_time 
        total_token_count += token_count
        total_token_count_wo_comments += token_count_wo_comments

        logger.info(f"YELLOW: Run time is {run_time}, Total Token Count is {token_count}, Total Token Count W/O Comments {token_count_wo_comments}")


    avg_run_time = total_run_time / len(python_scripts)
    avg_token_count = total_token_count / len(python_scripts)
    avg_token_count_wo_comments = total_token_count_wo_comments / len(python_scripts)

    logger.info(f"GREEN: [Python] Average Run time is {avg_run_time}, Token Count is {avg_token_count}, Token Count W/O Comments {avg_token_count_wo_comments}")


    total_run_time = 0
    total_token_count = 0
    total_token_count_wo_comments = 0

    for script in tqdm.tqdm(tcl_scripts):
        with open(script) as file:
            string = file.read()

        token_count, token_count_wo_comments = measure_token_count(
           string=string,
           model="gpt-3.5-turbo-0125"
        )

        run_time = measure_runtime(
            script=script, 
            odb_file=odb_file, 
            liberty_file=liberty_files,
            python=False
        )

        total_run_time += run_time 
        total_token_count += token_count
        total_token_count_wo_comments += token_count_wo_comments

        logger.info(f"YELLOW: Run time is {run_time}, Total Token Count is {token_count}, Total Token Count W/O Comments {token_count_wo_comments}")


    avg_run_time = total_run_time / len(tcl_scripts)
    avg_token_count = total_token_count / len(tcl_scripts)
    avg_token_count_wo_comments = total_token_count_wo_comments / len(tcl_scripts)

    logger.info(f"GREEN: [TCL] Average Run time is {avg_run_time}, Token Count is {avg_token_count}, Token Count W/O Comments {avg_token_count_wo_comments}")


    total_run_time = 0
    total_token_count = 0
    total_token_count_wo_comments = 0

    for query in tqdm.tqdm(test_design):
        token_count, _ = measure_token_count(
            string=query['ground_truth'][0]
        )

        run_time, _ = execute_query(
            query=query['ground_truth'][0],
            database=graph_database,
            use_cypher=True 
        )

        logger.info(f"YELLOW: Run time is {run_time}, Total Token Count is {token_count}, Total Token Count W/O Comments {token_count_wo_comments}")

        total_run_time += run_time 
        total_token_count += token_count
        total_token_count_wo_comments += token_count_wo_comments

    avg_run_time = total_run_time / len(test_design)
    avg_token_count = total_token_count / len(test_design)
    avg_token_count_wo_comments = total_token_count_wo_comments / len(test_design)

    logger.info(f"GREEN: [Cypher] Totlal Run time is {avg_run_time}, Token Count is {avg_token_count}, Token Count W/O Comments {avg_token_count_wo_comments}")


if __name__ == "__main__":
  main()
