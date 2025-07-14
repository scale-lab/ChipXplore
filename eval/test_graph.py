test_design = [
    # # #### Design Questions 
    {
        # usbc_core: floorplan: 298, placemet: 349, cts: 383, routing: 626
        "input": "Compare the number of buffer cells between the routing, placement, cts, and floorplan stages in the design",
        "stage": ["floorplan", 'placement', 'routing', 'cts'],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design)-[:CONTAINS_CELL]->(c:Cell) WHERE d.stage IN ['routing', 'placement', 'cts', 'floorplan'] AND c.is_buf = true RETURN d.stage, COUNT(c) as num_buffer_cells"
        ]
    },
    {
        # usbc_core: sky130_fd_sc_hd__dfrtp_4 
        "input": "What is the name of the cell that has the largest area in the design ?" ,
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name ORDER BY c.area DESC LIMIT 1"
        ]
    },
    {
        # usbc_core: 39401.3153
        "input": "What is the die area of this design ?", 
        "stage": ["floorplan"],
        "selected_nodes": ["Design"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'floorplan'}) RETURN d.die_area"
        ]
    },
    {
        # usbc_core: 32701.36319999901
        "input": "What is the total cell area of this design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN SUM(c.area)",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN SUM(toFloat(c.area))"
        ]
    },
    {
        # usbc_core: 2299+2=2301
        "input": "How many nets are available in this design ?",
        "stage": ["floorplan"],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN COUNT(n)"
        ]
    },
    {
        # usbc_core: 4669
        "input": "How many cells are available in this design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN COUNT(c)"
        ]
    },
    {
        # usbc_core: 55
        "input": "How many ports are available in this design ? ",
        "stage": ["floorplan"],
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'floorplan'})-[:HAS_PORT]->(n:Port) RETURN COUNT(n)"
        ]
    },
    # # ##### IOPort Questions
    {
        # usbc_core: 27
        "input": "How many input ports are present in the design ?",
        "stage": ["floorplan"], 
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (:Design {stage: 'floorplan'})-[:HAS_PORT]->(:Port {direction: 'INPUT'}) RETURN COUNT(*) as num_input_pins"
        ]
    },
    {
        # usbc_core: VGND, VPWR
        "input": "What is the name of the power and ground ports in the design ?",
        "stage": ["floorplan"], 
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'floorplan'})-[:HAS_PORT]->(p:Port) WHERE p.signal_type IN ['POWER', 'GROUND'] RETURN p.port_name"
        ]
    },
    {
        # usbc_core:  
        "input": "Which input ports are drawn on met3 layer in the design?",
        "stage": ["routing"], 
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE p.layer = 'met3' AND p.direction = 'INPUT' RETURN p.port_name",
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE p.layer = 'met3' AND p.direction = 'INPUT' RETURN p"
        ]
    },
    {
        #### usbc_core: utmi_txready_i  
        "input": "Which input port has the largest area in the design? Exclude power and ground pins",
        "stage": ["floorplan"], 
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'floorplan'})-[:HAS_PORT]->(dp:Port) WHERE dp.direction = 'INPUT' AND dp.signal_type <> 'POWER' AND dp.signal_type <> 'GROUND' RETURN dp.pin_name ORDER BY toFloat(dp.width) * toFloat(dp.height) DESC LIMIT 1;",
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE p.direction = 'INPUT' AND p.signal_type = 'SIGNAL' RETURN p.port_name, toFloat(p.width) * toFloat(p.height) AS area ORDER BY area DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE p.direction = 'INPUT' AND p.signal_type <> 'POWER' AND p.signal_type <> 'GROUND' RETURN p ORDER BY toFloat(p.width) * toFloat(p.height) DESC LIMIT 1"
        ]
    },
    {
        ### usbc_core: utmi_rxerror_i, utmi_dmpulldown_o #### 
        "input": "Which ports are placed on the bottom side of the design ? ",
        "stage": ["floorplan"],
        "selected_nodes": ["Design", "Port"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE p.y = d.ymin RETURN p"
        ]
    },
    # # #### Cells questions
    {
        # usbc_core: 626
        "input": "How many buffer cells are present in the design ?", 
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell {is_buf: true}) RETURN COUNT(c)"
        ]
    },
    {
        # usbc_core: 349
        "input": "How many inverters are present in the design ?",
        "stage": ["floorplan"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (:Design {stage: 'floorplan'})-[:CONTAINS_CELL]->(c:Cell {is_inv: true}) RETURN COUNT(c)"
        ]
    },
    {
        # usbc_core: 
            # - seq cells 302
            # - total cells: 4669
            # - percentage: 6.45
        "input": "What is the percentage of sequential cells in this design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WITH COUNT(c) AS totalCells, SUM(CASE WHEN c.is_seq = true THEN 1 ELSE 0 END) AS seqCells RETURN (toFloat(seqCells) / totalCells) * 100 AS percentageSequentialCells"
        ]
    },
    {
        # usbc_core: 336 cells
        "input": "How many cells are part of the clock tree network ?", 
        "stage": ['routing'],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell {is_in_clk: true}) RETURN count(c)"
        ]
    },
    {
        # usbc_core: 51.317
        "input": "What is the percentage of the physical only cells in the design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WHERE c.is_physical_only = true WITH count(c) AS physicalOnlyCells, size((d)-[:CONTAINS_CELL]->()) AS totalCells RETURN (physicalOnlyCells * 100.0) / totalCells AS percentage_physical_only_cells;"
        ]
    },
    {
        # usbc_core: sky130_fd_sc_hd__clkbuf_16
        "input": "Which cell has the largest dynamic power in the design? Return cell name",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name ORDER BY c.dynamic_power DESC LIMIT 1;",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name, c.dynamic_power ORDER BY c.dynamic_power DESC LIMIT 1"
        ]
    },

    {
        # usbc_core: sky130_fd_sc_hd__xnor2_2
        "input": "What is the name of the cell that has the largest static power in the design ?" ,
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name ORDER BY c.static_power DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.instance_name ORDER BY c.static_power DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.instance_name, c.static_power ORDER BY c.static_power DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) RETURN c.cell_name, c.static_power ORDER BY c.static_power DESC LIMIT 1"
        ]
    },
    {
        # usbc_core: sky130_fd_sc_hd__clkbuf_8
        "input": "What is the name of the cell that drives the largest number of other cells in the design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WITH c, SIZE((c)-[:DRIVES]->()) AS drivers ORDER BY drivers DESC LIMIT 1 RETURN c.cell_name",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WITH c, SIZE((c)-[:DRIVES]->()) AS drivers ORDER BY drivers DESC LIMIT 1 RETURN c",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WITH c, SIZE((c)-[:DRIVES]->()) AS drivers ORDER BY drivers DESC LIMIT 1 RETURN c.instance_name",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:DRIVES]->(c2:Cell) WITH c, COUNT(c2) AS numDrivenCells ORDER BY numDrivenCells DESC RETURN c.cell_name, numDrivenCells LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c1:Cell)-[:DRIVES]->(c2:Cell) RETURN c1.instance_name, COUNT(c2) AS num_driven ORDER BY num_driven DESC LIMIT 1"
        ]
    },
    # ### Cell Pin Questions
    {
        ### usbc_core: sky130_fd_sc_hd__nor3_1 #### 
        "input": "What is the name of the cell that has the largest output pin transition time in the design ?",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Cell", "CellInternalPin"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) RETURN c.cell_name ORDER BY p.pin_transition DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) RETURN c.instance_name ORDER BY p.pin_transition DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) RETURN c.cell_name, p.pin_transition ORDER BY p.pin_transition DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) WHERE p.direction = 'OUTPUT' RETURN c.instance_name, p.pin_transition ORDER BY p.pin_transition DESC LIMIT 1"
        ]
    },
    {
        ##### usbc_core: 0
        "input": "Are there any cells with negative pin slack ?",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Cell", "CellInternalPin"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(cp:CellInternalPin) WHERE cp.pin_slack < 0 RETURN c",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) WHERE p.pin_slack < 0 RETURN COUNT(p)"
        ]
    },
    {
        # usbc_core: conb_1
        "input": "Which cell has the largest output pin slack in the design ? Return cell name",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Cell", "CellInternalPin"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) RETURN c.cell_name ORDER BY p.pin_slack DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) RETURN c.cell_name, p.pin_slack ORDER BY p.pin_slack DESC LIMIT 1"
        ]
    },
    {
        ### usbc_core: sky130_fd_sc_hd__clkbuf_8
        "input": "Which cell in the design has the largest absolute difference between their rise and fall arrival times of its output pin?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Cell", "CellInternalPin"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) WITH c, ABS(p.pin_rise_arr - p.pin_fall_arr) AS time_diff RETURN c.cell_name ORDER BY time_diff DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) WITH c, ABS(p.pin_rise_arr - p.pin_fall_arr) AS time_diff RETURN c.instance_name ORDER BY time_diff DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {direction: 'OUTPUT'}) WITH c, ABS(p.pin_rise_arr - p.pin_fall_arr) AS arrival_time_difference RETURN c ORDER BY arrival_time_difference DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) WHERE p.direction = 'OUTPUT' RETURN c, abs(p.pin_rise_arr - p.pin_fall_arr) AS diff ORDER BY diff DESC LIMIT 1"
        ]
    },
    # ##### Net Questions
    {
        # usbc_core: clknet_2_0__leaf_clk_i
        "input": "Which net has the largest total capacitance ?",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [ 
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN n.net_name ORDER BY n.total_cap DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN n.net_name AS NetName, n.total_cap AS TotalCapacitance ORDER BY n.total_cap DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN n ORDER BY n.total_cap DESC LIMIT 1",
        ]
    },
    {
        # usbc_core: clknet_leaf_7_clk_i
        "input": "Which net has the largest fanout ? ",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN n.net_name ORDER BY n.fanout DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) RETURN n.net_name AS NetName, n.fanout AS Fanout ORDER BY n.fanout DESC LIMIT 1"
        ]
    },
    {
        # usbc_core: VGND
        "input": "Which net has the largest routed length ? Exclude power and gnd pins",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) WHERE n.signal_type <> 'POWER' AND n.signal_type <> 'GROUND' RETURN n.net_name, n.routed_length ORDER BY n.routed_length DESC LIMIT 1",
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) WHERE n.signal_type <> 'POWER' AND n.signal_type <> 'GROUND' RETURN n.net_name ORDER BY n.routed_length DESC LIMIT 1"
        ]
    },
    {
        # usbc_core: 5
        "input": "Retrieve the number of unique metal layers used for routing the nets in the design",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(:Net)-[:ROUTED_ON]->(s:Segment) RETURN COUNT(DISTINCT s.layer)"
        ]
    },
    {
        # usbc_core: 1093
        "input": "How many nets have length greater than 10 microns ?",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) WHERE n.routed_length > 10 RETURN COUNT(n)"
        ]
    },
    {
        # usbc_core: met2, met3, met4, met5
        "input": "Which metal layers are used for routing the power delivery network in the design? The power delivery network contains both the ground and power nets ",
        "stage": ['floorplan'],
        "selected_nodes": ["Design", "Net", "Segment"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net) WHERE n.signal_type IN ['POWER', 'GROUND'] MATCH (n)-[:ROUTED_ON]->(s:Segment) RETURN DISTINCT s.layer"
        ]
    },
    {
        # usbc_core: met3, met2, met1, met4
        "input": "Which metal layers are used for routing the clock net in the design ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Net", "Segment"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net {signal_type: 'CLOCK'})-[:ROUTED_ON]->(s:Segment) RETURN DISTINCT s.layer"
        ]
    },
    # ######## Graph Questions
    #         #### {
    #         ###### ubsc_core
    #         #####"input": "Which register-to-register path in this design contains the highest number of cells between the source and destination registers?",
    #         #####"stage": ['routing'],
    #         #####"selected_nodes": ["Design", "Cell"],
    #         #####"ground_truth": [
    #         #####"MATCH path=(s:Cell {is_seq: true})-[:DRIVES*]->(d:Cell {is_seq: true}) WHERE s <> d RETURN path ORDER BY LENGTH(path) DESC LIMIT 1"
    #         #####]
    #         #####},
    {   ### usbc_core: 0
        "input": "How many cells are electrically isolated (not connected to any nets) ?",
        "stage": ['routing'],
        "selected_nodes": ["Design", "Cell", "Net"],
        "ground_truth": [
            " MATCH (d:Design {stage: 'routing'})-[:CONTAINS_CELL]->(c:Cell) WHERE NOT (c)-[:CONNECTS_TO]->(:Net) RETURN COUNT(c)"
        ]
    },
    {
        ### usbc_core: 4
        "input": "How many ports are unconnected in the design ?", 
        "stage": ["routing"], 
        "selected_nodes": ["Design", "Port", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port) WHERE NOT (p)-[:DRIVES_NET]->(:Net) AND NOT (:Net)-[:CONNECTS_TO]->(p) RETURN COUNT(p)",
        ]
    },
    {
        # usbc_core: sky130_fd_sc_hd__buf_1
        "input": "What is the name of the cell that is connected to the rst_i port ?",
        "stage": ["routing"],
        "selected_nodes": ["Design", "Port", "Cell", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port {port_name: 'rst_i'})-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c:Cell) RETURN c",
            "MATCH (d:Design {stage: 'routing'})-[:HAS_PORT]->(p:Port {port_name: 'rst_i'})-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c:Cell) RETURN c.cell_name"
        ]
    },
    {
        # usbc_core: 
        "input": "How many cells are connected to the clock net ?",
        "stage": ["routing"],
        "selected_nodes": ["Design",  "Cell", "Net"],
        "ground_truth": [
            "MATCH (d:Design {stage: 'routing'})-[:CONTAINS_NET]->(n:Net {signal_type: 'CLOCK'})-[:CONNECTS_TO]->(c:Cell) RETURN COUNT(c)",
        ]
    },
]