""""Evaluation metrics for the agent performance:
    - Execution Accuracy (EA): 
        EX is defined as the proportion of examples in the evaluation set for
        which the executed results of both the predicted and ground-truth SQLs are identical, relative to the
        overall number of SQLs
        https://arxiv.org/pdf/2305.03111
    
    - Valid Efficiency Score (VES):
        VES is designed to measure the efficiency of valid SQLs generated
        by models. It is worth noting that the term "valid SQLs" refers to predicted SQL queries whose
        result sets align with those of the ground-truth SQLs. Any SQL queries that fail to fetch the correct
        values will be declared invalid since they are totally useless if they cannot fulfill the user requests,
        regardless of their efficiency. In this case, the VES metric considers both the efficiency and accuracy
        of execution results
    
    Based on : 
        - (ves) https://github.com/AlibabaResearch/DAMO-ConvAI/blob/main/bird/llm/src/evaluation_ves.py
        - (ex) https://github.com/AlibabaResearch/DAMO-ConvAI/blob/ac710949bcdb7ea253e0cfe57f063bb3f50bb86c/bird/llm/src/evaluation.py
"""

import time
import math
import sqlite3
import neo4j
import sqlalchemy
import numpy as np 
from langchain_community.graphs import Neo4jGraph
from neo4j.exceptions import Neo4jError

from core.database.graphdb import URI, USER, PASSWORD


def tuple_to_sorted_list(t):
    return sorted(list(t), key=lambda x: (isinstance(x, str), x))


def dict_to_list(input_dicts):
    def make_hashable(item):
        if isinstance(item, dict):
            return frozenset((k, make_hashable(v)) for k, v in item.items())
        elif isinstance(item, list):
            return tuple(make_hashable(i) for i in item)
        return item

    return set(make_hashable(item) for item in input_dicts)


def extract_values(result) -> list:
    def flatten(item) -> list:
        if isinstance(item, (list, frozenset)):
            return [val for subitem in item for val in flatten(subitem)]
        elif isinstance(item, tuple):
            # Assuming tuples are key-value pairs, only process the value (index 1)
            if len(item) >= 1:
                return flatten(item[1])
            else:
                return [item]
        elif isinstance(item, dict):
            return [val for pair in sorted(item.items()) for val in flatten(pair)]
        else:
            return [item]

    return flatten(result)


def normalize(data: list) -> list:
    """Normalize the data structure for consistent comparison."""
    if isinstance(data, list):
        return sorted(normalize(item) for item in data)
    elif isinstance(data, tuple):
        return tuple(normalize(item) for item in data)
    else:
        return data



def execute_query(query, database, use_cypher=False):
    if not query:
        return 0, set([])  
    
    try: 
        if use_cypher: 
            start_time = time.time()
            query_result =  database.query(query) 
            query_result = dict_to_list(query_result)
            exec_time = time.time() - start_time
            print(f"Query Result is {query_result}")
            query_result = extract_values((list(query_result)))
        else:
            start_time = time.time()
            query_result = database.run(query)
            exec_time = time.time() - start_time
            print(f"Query Result is {query_result}")
            query_result = {tuple(tuple_to_sorted_list(t)) for t in query_result}
    except (TypeError, sqlalchemy.exc.OperationalError, sqlalchemy.exc.StatementError, sqlite3.OperationalError, sqlite3.Warning,  Neo4jError, neo4j.exceptions.CypherSyntaxError, ValueError, sqlalchemy.exc.InvalidRequestError) as e: 
        print(f"Encoutered Error: {e} during Queyr Execution!!!!")
        return 0, set([]) 
    
    return exec_time, query_result


def clean_abnormal(input):
    input = np.asarray(input)
    processed_list = []
    mean = np.mean(input, axis=0)
    std = np.std(input, axis=0)
    for x in input:
        if x < mean + 3 * std and x > mean - 3 * std:
            processed_list.append(x)
    return processed_list


def measure_time_ratio(predicted_sql, ground_truth, database, num_iters=1, use_cypher=False):
    diff_list = []
    
    if predicted_sql is None:
        return 0 
    
    predicted_time, pred_res = execute_query(predicted_sql, database, use_cypher=use_cypher)

    passed = False
    for ground_truth_sql in ground_truth: 
        ground_truth_time, ground_truth_res = execute_query(ground_truth_sql, database, use_cypher=use_cypher) 

        if set(pred_res) == set(ground_truth_res): 
            passed = True 
            
    if passed: 
        for _ in range(num_iters):
            predicted_time, _ = execute_query(predicted_sql, database, use_cypher=use_cypher)
            ground_truth_time, _ = execute_query(ground_truth[0], database, use_cypher=use_cypher) 
            if predicted_time is None:
                diff_list.append(1)
            else: 
                diff_list.append(ground_truth_time / predicted_time)

    if len(diff_list) != 0 : 
        processed_diff_list = clean_abnormal(diff_list)
        if len(processed_diff_list) != 0: 
            time_ratio = sum(processed_diff_list) / len(processed_diff_list)
        else:
            time_ratio = 0
    else: 
        time_ratio = 0
   
    return time_ratio


def compute_ves(predicted_queries, ground_truth, database, num_iters=1, use_cypher=False):
    time_ratios = []
    for pred_query, ground_truth_query in zip(predicted_queries, ground_truth):

        time_ratio = measure_time_ratio(pred_query, ground_truth_query, database, num_iters=num_iters, use_cypher=use_cypher)
        time_ratios.append(time_ratio)
        
    num_queries = len(predicted_queries)

    total_ratio = 0
    count = 0
    for i, result in enumerate(time_ratios):
        if result != 0:
            count += 1
        total_ratio += math.sqrt(result) * 100

    if num_queries !=0 :
        ves = (total_ratio/num_queries)
    else: 
        ves = 0
    return ves 



def compute_execution_acc(predicted_queries, ground_truth_queries, database, use_cypher=False):
    results = []
    num_queries = len(predicted_queries)

    for pred_query, ground_truth_query in zip(predicted_queries, ground_truth_queries): 
        print("Ground Truth: ", ground_truth_query)
        print("Predicted Query: ", pred_query)
        if pred_query is None: 
            continue 
        _, pred_res = execute_query(pred_query, database, use_cypher=use_cypher)

        for ground_truth in ground_truth_query: 
            _, ground_truth_res = execute_query(ground_truth, database, use_cypher=use_cypher)

            # print(f"Prediction Result: {db_path.run(pred_query)}, Ground Truth: {db_path.run(ground_truth)}")
            if set(pred_res) == set(ground_truth_res):
                results.append(1)
                break 
    
    acc = sum(results) / num_queries if num_queries != 0 else 0
 
    return acc 


__all__ = [
    'execute_query', 
    'compute_execution_acc',
    'compute_ves'
]

def main():
    num_iters = 100
    predicted_sqls = [
        "SELECT Name, Area FROM Cells ORDER BY Area ASC LIMIT 1 OFFSET 1",
        "SELECT CellVariant FROM ( SELECT CellVariant, MIN(SizeWidth) AS MinWidth FROM Macros WHERE Name LIKE '%__mux4_1' GROUP BY CellVariant ) AS SubQuery ORDER BY MinWidth ASC LIMIT 1",
        "SELECT (SELECT SizeHeight FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND CellVariant = 'sky130_fd_sc_hs') AS HighSpeedHeight, (SELECT SizeHeight FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND CellVariant = 'sky130_fd_sc_ls') AS LowSpeedHeight, (SELECT SizeHeight FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND CellVariant = 'sky130_fd_sc_ms') AS MediumSpeedHeight"
    ]
    
    ground_truth_sqls = [
       ["SELECT Area, Name FROM Cells ORDER BY Area ASC LIMIT 1 OFFSET 1"],
       ["SELECT SizeWidth, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' OR Name = 'sky130_fd_sc_ms__nand2_1'", "SELECT (SELECT SizeWidth FROM Macros WHERE MacroID = (SELECT MacroID FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND CellVariant = 'sky130_fd_sc_hd')) AS Width_HighDensity, (SELECT SizeWidth FROM Macros WHERE MacroID = (SELECT MacroID FROM Macros WHERE Name = 'sky130_fd_sc_ms__nand2_1' AND CellVariant = 'sky130_fd_sc_ms')) AS Width_MediumSpeed", "SELECT Name, SizeWidth, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND CellVariant = 'sky130_fd_sc_hd' UNION SELECT Name, SizeWidth, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_ms__nand2_1' AND CellVariant = 'sky130_fd_sc_ms'"],
       ["SELECT Name, SizeHeight FROM Macros WHERE Name IN ('sky130_fd_sc_hs__a31oi_1', 'sky130_fd_sc_ls__a31oi_1', 'sky130_fd_sc_ms__a31oi_1') AND CellVariant IN ('sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms')", "SELECT Name, SizeHeight, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND CellVariant = 'sky130_fd_sc_hs' UNION SELECT Name, SizeHeight, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND CellVariant = 'sky130_fd_sc_ls' UNION SELECT Name, SizeHeight, CellVariant FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND CellVariant = 'sky130_fd_sc_ms'", "SELECT 'High Speed' AS Library, SizeHeight AS Height FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND CellVariant = 'sky130_fd_sc_hs' UNION SELECT 'Low Speed' AS Library, SizeHeight AS Height FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND CellVariant = 'sky130_fd_sc_ls' UNION SELECT 'Medium Speed' AS Library, SizeHeight AS Height FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND CellVariant = 'sky130_fd_sc_ms'"]
    ]
    
    db_path = "dbs/sky130.db"
    
    ves = compute_ves(predicted_sqls, ground_truth_sqls, db_path, num_iters=num_iters) 
    ex = compute_execution_acc(predicted_sqls, ground_truth_sqls, db_path)
    
    print(f"SQL VES: {ves}, SQL EX: {ex}")
    
    # Cypher
    graph_database = Neo4jGraph(url=URI, username=USER, password=PASSWORD, enhanced_schema=True) 

    predicted_cyphers = [
        "MATCH (n:Net) RETURN n ORDER BY n.total_cap DESC LIMIT 1",
        "MATCH (d:Design) WHERE d.name = 'spm' RETURN COUNT(DISTINCT d.stage) as num_physical_design_stages;",
        "MATCH (d:Design {stage: 'routing'})-[:CONNECTED_TO]->(c:Cell) RETURN SUM(toFloat(c.area)) AS total_cell_area;"
    ]
    
    ground_truth_cyphers = [
        ["MATCH (n:Net) RETURN n ORDER BY n.total_cap DESC LIMIT 1;"],
        ["MATCH (d:Design) WHERE d.name = 'spm' RETURN COUNT(DISTINCT d.stage) as num_physical_design_stages;"],
        ["MATCH (d:Design {stage: 'routing'})-[:CONNECTED_TO]->(c:Cell) RETURN SUM(toFloat(c.area)) AS total_cell_area;"]
    ]

    ves = compute_ves(predicted_cyphers, ground_truth_cyphers, graph_database, num_iters=num_iters, use_cypher=True) 
    ex = compute_execution_acc(predicted_cyphers, ground_truth_cyphers, graph_database, use_cypher=True)

    print(f"Cypher VES: {ves}, Cypher EX: {ex}")

    
if __name__ == '__main__':
    main()
    
