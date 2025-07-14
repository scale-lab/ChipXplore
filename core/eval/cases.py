"""Test the framework using a number of hardware design scenarios
"""

pdk_design_cases = [
    {
      "input": "What would be the total increase in area and static power if we replaced all the buffer cells connected to the 'rst_i' net in the current design with the buf_2 cell from the high speed library in the PDK ?",
      "scl_variant": "HighSpeed",
      "sql_query": [
         "SELECT Area FROM Cells WHERE Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hs' ) AND Name = 'sky130_fd_sc_hs__buf_2'"
      ],
      "cypher_query": [
         "MATCH (d:Design {stage: 'placement'})-[:CONTAINS_CELL]->(c:Cell {cell_name: 'sky130_fd_sc_hd__buf_2'}) RETURN COUNT(c) AS instance_count"
      ]
   },
#    {
#       "input": "What would be the area impact of replacing all flip-flops cell in our design with the scan-enabled flip-flop cell named 'sdfbbn_2' from the high density library?", 
#       "scl_variant": "HighDensity",
#       "sql_query": [  
#          "SELECT Area FROM Cells WHERE Name = 'sky130_fd_sc_hd__sdfbbn_2' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd' );",
#       ],
#       "stage": ['routing'],
#       "cypher_query": [
#          "MATCH (d:Design {stage: 'cts'})-[:CONTAINS_CELL]->(c:Cell {is_seq: true}) RETURN c.cell_name AS FlipFlopType, COUNT(c) AS Quantity, c.area AS Area"
#       ]
#    },
#    {
#         "input": "What is the static power and area impact of replacing the top 5 cells with the highest static power in the design with their corresponding cells from the low leakage library ? ",
#         "scl_variant": "HighDensityLowLeakage",
#         "sql_query": [
#             "SELECT Leakage_Power AS Static_Power FROM Cells WHERE Name = 'sky130_fd_sc_hdll__clkbuf_16' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hdll' );",
#         ],
#         "stage": ['routing'],
#         "cypher_query": [
#             "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name AS CellName, c.static_power AS StaticPower ORDER BY c.static_power DESC LIMIT 1"
#         ]
#    },
  
]


design_cases = [
    {
        # Error Detection and Resolution: Identify unconnected components 
        "input": "List any unconnected cells or ports in the design",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WHERE NOT (c)-[:CONNECTED_TO]->(:Net) RETURN c AS unconnectedEntity UNION MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE NOT ((p)-[:DRIVES_NET]->(:Net) OR (:Net)-[:CONNECTS_TO]->(p)) RETURN p AS unconnectedEntity",
        ]
    },
    {
        # Net analysis 
        "input": "List nets that exceed these thresholds: routed length > 190 microns or fanout > 20. Also analyze the clock net's fanout, routed length, and metal layers. Exclude power and ground nets.",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell", "Net", ""],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) WHERE n.routed_length > 190 OR n.fanout > 20 RETURN n.id AS NetID, n.net_name AS NetName, n.routed_length AS RoutedLength, n.fanout AS Fanout, NULL AS Layer UNION MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net {signal_type: 'CLOCK'})-[:ROUTED_ON]->(s:Segment) RETURN n.id AS NetID, n.net_name AS NetName, n.routed_length AS RoutedLength, n.fanout AS Fanout, COLLECT(s.layer) AS Layer",
        ]
    },
    {
        # Stage analysis 
        "input": "Summarize the changes between the design stages in terms of total static and dynamic power, number of buffer cells, inverter cells, and physical only cells.",
        "stage":  ['floorplan', 'placement', 'cts', 'routing'],
        "selected_nodes": ["Design", "Cell", "Net"],
        "ground_truth": [
            "MATCH (d:Design)-[:CONTAINS_CELL]->(c:Cell) WHERE d.stage IN ['floorplan', 'placement', 'cts', 'routing'] RETURN d.stage AS Stage, SUM(c.static_power) AS Total_Static_Power, SUM(c.dynamic_power) AS Total_Dynamic_Power, COUNT(c) AS Total_Cells, SUM(CASE WHEN c.is_buf = true THEN 1 ELSE 0 END) AS Buffer_Cells, SUM(CASE WHEN c.is_inv = true THEN 1 ELSE 0 END) AS Inverter_Cells, SUM(CASE WHEN c.is_physical_only = true THEN 1 ELSE 0 END) AS Physical_Only_Cells ORDER BY CASE d.stage WHEN 'floorplan' THEN 1 WHEN 'placement' THEN 2 WHEN 'cts' THEN 3 WHEN 'routing' THEN 4 END",
        ]
    }
]

pdk_cases = [
    {
        "input": "Retrieve the width, resistance, DC/AC current density, and capacitance values for each metal layer in the PDK, ordered from thickest to thinnest layer, across the different operating corners.",
        "view": "TechnologyLef",
        "selected_tables": ['Routing_Layers'],
        "scl_variant": ['HighDensity'],
        "op_cond": ["nom", 'min', 'max'],
        "ground_truth": [
            "SELECT Name, Width, Resistance_Per_SQ, DC_Current_Density_Avg, AC_Current_Density_Rms, Capacitance_Per_SQ_Dist, Thickness, Corner FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('min', 'nom', 'max') ORDER BY Thickness DESC;"
        ]
    },
    {
        "input": "Compare the leakage power, clock pin capacaitance, area, and average propagation delay of the flip-flop cells with a drive strenght of 4 across the different libraries in the PDK. ",
        "view": "Liberty",
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "scl_variant": ['HighDensity', 'HighDensityLowLeakage', 'HighSpeed', 'LowSpeed', 'MediumSpeed', 'LowPower'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Name, Width, Resistance_Per_SQ, DC_Current_Density_Avg, AC_Current_Density_Rms, Capacitance_Per_SQ_Dist, Thickness, Corner FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('min', 'nom', 'max') ORDER BY Thickness DESC;"
        ]
    },
    # {
    #     "input": "What is the lowest leakage power flip flop across the high density, high density low leakage, and low power libraries? ",
    #     "view": "lib",
    #     "selected_tables": ['Operating_Conditions', 'Cells'],
    #     "scl_variant": ['HighSpeed', 'HighDensity'],
    #     "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
    #     "ground_truth": [
    #         "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs');"
    #     ]
    # },
    # {
    #     "input": "Compare the width for the mux4_1 cell across all libraries ?",
    #     "view": "lef",
    #     "scl_variant": ['HighSpeed', 'HighDensity'],
    #     'selected_tables': ['Macros'],
    #     "ground_truth": 
    #     [
    #         "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs');"
    #     ]
    # },
]


