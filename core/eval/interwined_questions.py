# Interwined Questions that require querying both databases 
test_queries_interwined = [
    {
        #
        "input": "How many metal layers does our current design use, and how does this compare to the number of metal layers available in the PDK?",
        "scl_variant": "HighDensity",
        "sql_query": [
            "SELECT COUNT(DISTINCT Name) AS MaxMetalLayers FROM RoutingLayers WHERE CellVariant = 'sky130_fd_sc_hd' AND Corner = 'nom'"
        ],
        "stage": ['routing'],
        "cypher_query": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_OUTPUT_PIN]->(cp:CellPin)-[:DRIVES_NET]->(n:Net) RETURN DISTINCT n.layers as metal_layers_used"
        ]
    },
    # {
    #     # while 'met3' is used for routing the clock net and is one of the thicker layers available in the PDK, it is not the thickest. The thickest layer, 'met5', is not utilize
    #   "input": "Which metal layers are used for routing the clock net in the design and how does this compare to the thickest metal layer in the PDK ?",
    #   "scl_variant": "HighDensity",
    #   "sql_query": [   
    #      "SELECT COUNT(DISTINCT Name) AS Number_of_Unique_Standard_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd')"
    #   ],
    #   "stage": ['routing'],
    #   "cypher_query": [
    #      "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell) RETURN COUNT(DISTINCT c.cell_name) as unique_standard_cell_instances"
    #   ]
    # },
    # {
    #     # ould result in an increase in the total area by 4833.4616 square microns.
    #     "input": "What would be the area impact of replacing all flip-flops cell in our design with the scan-enabled flip-flop cell named 'sdfbbn_2' from the high density library?", 
    #     "scl_variant": "HighDensity",
    #     "sql_query": [  
    #         "SELECT Area FROM Cells WHERE Name = 'sky130_fd_sc_hd__sdfbbn_2' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd' );",
    #     ],
    #     "stage": ['routing'],
    #     "cypher_query": [
    #         "MATCH (d:Design {stage: 'cts'})-[:CONTAINS_CELL]->(c:Cell {is_seq: true}) RETURN c.cell_name AS FlipFlopType, COUNT(c) AS Quantity, c.area AS Area"
    #     ]
    # },
    # {
    #     #\text{Increase in Area} = 5002.152 - 4770.8256 = 231.3264 \text{ square microns}
    #   "input": "What would be the total increase in area if we replaced all the buffer cells in the current design with the buf_2 cell from the high speed library in the PDK ?",
    #   "scl_variant": "HighSpeed",
    #   "sql_query": [
    #      "SELECT Area FROM Cells WHERE Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hs' ) AND Name = 'sky130_fd_sc_hs__buf_2'"
    #   ],
    #   "cypher_query": [
    #      "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell {cell_name: 'sky130_fd_sc_hd__buf_2'}) RETURN COUNT(c) AS instance_count"
    #   ]
    # },
    # {
    #     # - **Increase**: `35.0336 - 32.531200000000006 = 2.5024` (approximately 7.7% increase)
    #     "input": "What is the static power and area impact of replacing the top 2 cells with the highest static power in the design with their corresponding cells from the low leakage library ? ",
    #     "scl_variant": "HighDensityLowLeakage",
    #     "sql_query": [
    #         "SELECT Leakage_Power AS Static_Power, Area FROM Cells WHERE Name = 'sky130_fd_sc_hdll__xnor2_2' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll' );",
    #     ],
    #     "stage": ['routing'],
    #     "cypher_query": [
    #         "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c ORDER BY c.static_power DESC LIMIT 2"
    #     ]
    # },
    # {
    #   # \text{Percentage} = \left( \frac{106}{428} \right) \times 100 \approx 24.77\%
    #   "input": "How many unique standard cells from the PDK are we using in our current design, and what percentage of the total available cells in the PDK does this represent?",
    #   "scl_variant": "HighDensity",
    #   "sql_query": [   
    #      "SELECT COUNT(DISTINCT Name) AS Number_of_Unique_Standard_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd')"
    #   ],
    #   "stage": ['routing'],
    #   "cypher_query": [
    #      "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell) RETURN COUNT(DISTINCT c.cell_name) as unique_standard_cell_instances"
    #   ]
    # },
  
    # {
    #     # 1310.0064 - 1310.5064 = -0.5 \text{ square micrometers}
    #     "input": "If we replaced all inverters in our design with the smallest inverter from the PDK, how much area would we save?",
    #     "scl_variant": "HighDensity",
    #     "sql_query": [
    #         "SELECT Area FROM Cells WHERE Name = 'sky130_fd_sc_hd__inv_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Variant = 'sky130_fd_sc_hd');"
    #     ],
    #     "stage": ['placement'],
    #     "cypher_query": [
    #         "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell) WHERE c.cell_name CONTAINS 'inv' RETURN COUNT(c) as inverter_count, SUM(c.area) as current_area"
    #     ]
    # },
    # {
    #     # So, the area saved would be approximately 4770.83 - 2347.5 = 2423.33 square units.
    #     "input": "If we replaced all buffers in our design with the smallest buffer from the PDK, how much area would we save?",
    #     "scl_variant": "HighDensity",
    #     "sql_query": [
    #         "SELECT Area FROM Cells WHERE Name = 'sky130_fd_sc_hd__inv_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Variant = 'sky130_fd_sc_hd');"
    #     ],
    #     "stage": ['placement'],
    #     "cypher_query": [
    #         "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell) WHERE c.cell_name CONTAINS 'inv' RETURN COUNT(c) as inverter_count, SUM(c.area) as current_area"
    #     ]
    # }
]