from core.database.graphdb import get_node_descr, get_relationship_descr_verbose

examples = [
    {
        "question": "What is the average fanout of nets in the design?",
        "stage": "['routing']",
        "query": "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) RETURN AVG(n.fanout)",
        "subquestions": [
            "What is the fanout of each net in the design?",
            "How do we calculate the average fanout across all nets?"
        ],
        "subqueries": [
            "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) RETURN n.fanout",
            "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) RETURN AVG(n.fanout)" 
        ],
        "schema": get_node_descr(["Design", "Net"]),
        "relationship": get_relationship_descr_verbose(["Design", "Net"])
    },
    {
        "question": "What is the total static power consumption of all cells in the design?",
        "stage": "['routing']",
        "query": "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) RETURN SUM(c.static_power)",
        "subquestions": [
            "What is the static power consumption of each cell?",
            "How do we sum up the static power consumption across all cells?"
        ],
        "subqueries": [
            "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) RETURN c.static_power",
            "MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) RETURN SUM(c.static_power)"
        ],
        "schema": get_node_descr(["Design", "Cell"]),
        "relationship": get_relationship_descr_verbose(["Design", "Cell"])
    },
    {
        "question": "How many macro cells are present in the design?",
        "stage": "['placement']",
        "query": "MATCH (d:Design {{stage: 'placement'}})-[:CONTAINS_CELL]->(c:Cell) WHERE c.is_macro = true RETURN COUNT(c)",
        "subquestions": [
          "What defines a macro cell in the design?",
          "How do we count the number of macro cells?"  
        ],
        "subqueries": [
            "MATCH (d:Design {{stage: 'placement'}})-[:CONTAINS_CELL]->(c:Cell) WHERE c.is_macro = true RETURN c",
            "MATCH (d:Design {{stage: 'placement'}})-[:CONTAINS_CELL]->(c:Cell) WHERE c.is_macro = true RETURN COUNT(c)"
        ],
        "schema": get_node_descr(["Design", "Cell"]),
        "relationship": get_relationship_descr_verbose(["Design", "Cell"])
    },
]


def decompose(examples):
    examples_wdecompose = [] 
    for example in examples: 
        decompose_str = ""
        for i, (subquestion, subquery) in enumerate(zip(example['subquestions'], example['subqueries'])):
            decompose_str += f"""
Subquestion {i+1}: {subquestion}
Cypher 
```cypher 
{subquery}
```
"""

        decompose_str += f"""
Final Cypher is: 
Cypher
```cypher
{example['query']}
```

Question Solved.
"""
        example['decompose_str'] = decompose_str 
        del example['subquestions']
        del example['subqueries']
        examples_wdecompose.append(example)
        
    return examples_wdecompose 


cypher_generator_few_shot = decompose(examples)
