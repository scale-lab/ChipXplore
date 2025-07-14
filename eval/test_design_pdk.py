### test design pdk interactions 
test_design_pdk = [
   {
      "input": "What would be the area impact of replacing all flip-flops cell in our design with the scan-enabled flip-flop cell named 'sdfbbn_2' from the high density library?", 
      "scl_variant": "HighDensity",
      "sql_query": [  
         "SELECT Area FROM Cells WHERE Name = 'sky130_fd_sc_hd__sdfbbn_2' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd' );",
      ],
      "stage": ['routing'],
      "cypher_query": [
         "MATCH (d:Design {stage: 'cts'})-[:CONTAINS_CELL]->(c:Cell {is_seq: true}) RETURN c.cell_name AS FlipFlopType, COUNT(c) AS Quantity, c.area AS Area"
      ]
   },
   {
      "input": "How many unique standard cells from the PDK are we using in our current design, and what percentage of the total available cells in the PDK does this represent?",
      "scl_variant": "HighDensity",
      "sql_query": [   
         "SELECT COUNT(DISTINCT Name) AS Number_of_Unique_Standard_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd')"
      ],
      "stage": ['routing'],
      "cypher_query": [
         "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell) RETURN COUNT(DISTINCT c.cell_name) as unique_standard_cell_instances"
      ]
   },
   {
      "input": "How many metal layers does our current design use, and how does this compare to the maximum number of metal layers available in the PDK?",
      "scl_variant": "HighDensity",
      "sql_query": [
         "SELECT COUNT(DISTINCT Name) AS MaxMetalLayers FROM RoutingLayers WHERE CellVariant = 'sky130_fd_sc_hd' AND Corner = 'nom'"
      ],
      "stage": ['routing'],
      "cypher_query": [
         "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_OUTPUT_PIN]->(cp:CellPin)-[:DRIVES_NET]->(n:Net) RETURN DISTINCT n.layers as metal_layers_used"
      ]
   },
   {
      "input": "What would be the total increase in area if we replaced all the buffer cells in the current design with the buf_2 cell from the high speed library in the PDK ?",
      "scl_variant": "HighSpeed",
      "sql_query": [
         "SELECT Area FROM Cells WHERE Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hs' ) AND Name = 'sky130_fd_sc_hs__buf_2'"
      ],
      "cypher_query": [
         "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell {cell_name: 'sky130_fd_sc_hd__buf_2'}) RETURN COUNT(c) AS instance_count"
      ]
   },
   {
      "input": "What is the static power and area impact of replacing the top 10 cells with the highest static power in the design with their corresponding cells from the low leakage library ? ",
      "scl_variant": "HighDensityLowLeakage",
      "sql_query": [
         "SELECT Leakage_Power AS Static_Power FROM Cells WHERE Name = 'sky130_fd_sc_hdll__clkbuf_16' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hdll' );",
      ],
      "stage": ['routing'],
      "cypher_query": [
         "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name AS CellName, c.static_power AS StaticPower ORDER BY c.static_power DESC LIMIT 1"
      ]
   },
]