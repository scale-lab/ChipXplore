"""Runs openroad to parse design files at different physical design stages.
"""
import os
import json
import glob
import time
import argparse
import shlex
import subprocess
import signal
from core.database.graphdb import Neo4jConnection


def run_openroad_command(script_path, args, python=True, timeout=600):
    current_dir = os.getcwd()

    if python: 
        base_command = f"PYTHONPATH=/home/manar/python/lib/python3.9/site-packages:$(pwd) openroad -exit -python {script_path}"
    else:
        base_command = f"PYTHONPATH=/home/manar/python/lib/python3.9/site-packages:$(pwd) openroad -exit {script_path}"

    if python: 
        arg_list = []
        for arg_name, arg_value in vars(args).items():
            if isinstance(arg_value, list):
                arg_list.append(f"--{arg_name} {shlex.quote(','.join(arg_value))}")
            elif arg_value:
                arg_list.append(f"--{arg_name} {shlex.quote(str(arg_value))}")

        base_cmd_list = shlex.split(base_command)
        full_command_list = base_cmd_list + arg_list
    else:
        base_cmd_list = shlex.split(base_command)
        full_command_list = base_cmd_list 
        
    # print(f"Executing command: {' '.join(full_command_list)}")
   
    env = os.environ.copy()
    env.update({"PYTHONPATH": "/home/manar/python/lib/python3.9/site-packages:$(pwd)"})

    try:
        process = subprocess.Popen(' '.join(full_command_list), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid, env=env)

        start_time = time.time()
        while True:
            try:
                stdout, stderr = process.communicate(timeout=5)  # Wait for 5 seconds
                return_code = process.returncode
                break
            except subprocess.TimeoutExpired:
                if time.time() - start_time > timeout:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the signal to the process group
                    print(f"Error: OpenROAD command timed out after {timeout} seconds")
                    return None
                print("Command still running...")

        if return_code != 0:
            print(f"Error: OpenROAD command failed with return code {return_code}")
            print("Standard Error:")
            print(stderr)
            return None
        return stdout
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")
        return None


def run_parse_design(input, stage, pdk, bulk_format, output_dir):
    args = argparse.Namespace(
        input=input,
        stage=stage,
        pdk=pdk,
        format='bulk' if bulk_format else 'load',
        output_dir=output_dir
    )
    result = run_openroad_command("core/parsers/design/design_parser.py", args)
    try:
        print(f"Result is: {result}")
        design_info = json.loads(result)
        return design_info
    except json.JSONDecodeError:
        print("Error parsing JSON output:")
        print(result)
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, help='Path to design files', default='./designs/spm-small')
    parser.add_argument('--pdk', type=str, help='Path to PDK', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--use_bulk_import', help='Use bulk import for creating the graphdb', action='store_true', default=False)
    parser.add_argument('--output_dir', type=str, help='Path to output files', default='./output')
    args = parser.parse_args()

    input_dir = args.input
    pdk_path = args.pdk
    use_bulk_import = args.use_bulk_import 
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Parse design files using opendb
    stages = ['floorplan', 'placement', 'cts', 'routing']
    start_time = time.time()
    for stage in stages:
        def_file = glob.glob(os.path.join(input_dir, stage, '*.def'))[0]
        sdc_file = glob.glob(os.path.join(input_dir, stage, '*.sdc'))[0]
        spef_file = glob.glob(os.path.join(input_dir, stage, '*.spef'))

        if len(spef_file) > 0:
            spef_file = spef_file[0]
        else:
            spef_file = ''

        design_info = run_parse_design(
            stage=stage,
            input=input_dir,
            pdk=pdk_path,
            bulk_format=use_bulk_import,
            output_dir=os.path.join(output_dir, stage)
        )

        if design_info:
            print(f"Design name: {design_info['name']}")
            print(f"Number of cells: {len(design_info['cells'])}")
            print(f"Number of nets: {len(design_info['nets'])}")
            print(f"Number of I/O ports: {len(design_info['io_ports'])}")

    
    #2. Load CSV files into neo4j database
    print("Clearing Database")
    conn = Neo4jConnection()
    conn.test_connection()
    conn.clear_database()

    print("Done Clearning Database")
    
    if not use_bulk_import: 
        for stage in stages: 
            conn.load_nodes_and_relationships(
                stage, 
                'cells.csv', 
                'pins.csv', 
                'nets.csv', 
                'segment.csv',
                'edges.csv', 
                'designs.csv', 
                'ioports.csv'
            )
    else:
        conn.bulk_import_nodes_and_relationships(stages)
        
    end_time = time.time()
    print("Database Creation time: ", end_time - start_time)

if __name__ == "__main__":
    main()