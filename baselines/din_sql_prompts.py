
##### SQL SCHEMA LINKERS ########

SCHEMA_LINKER_SYS_PROMPT = lambda lef_table_info, lef_table_descr, lef_fk_str, tlef_table_info, tlef_table_descr, tlef_fk_str, lib_table_info, lib_table_descr, lib_fk_str: f"""
You are an agent designed to find the schema_links for generating SQL queries for each question based on the database schema and Foreign keys.
The schema_links should include the relevant tables, columns, and their relationships needed to answer the question.

###
Few examples of this task are:
###
Schema of the LEF database with sample rows and column descriptions:
#

{lef_table_info}
{lef_table_descr}


Foreign Keys:
{lef_fk_str}

Q: "Find all macros with width greater than 2.0 from the high density library."
A: Let's think step by step. In the question "Find all macros with width greater than 2.0 from the high density library'sky130_fd_sc_hd'", we are asked:
"all macros" so we need table = [Macros]
"with width greater than 2.0" so we need column = [Macros.Size_Width]
"from the sky130_fd_sc_hd library" so we need column = [Macros.Cell_Library]
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [2.0, 'sky130_fd_sc_hd'].
So the Schema_links are:
Schema_links: [Macros.*, Macros.Size_Width, 2.0, Macros.Cell_Library, 'sky130_fd_sc_hd']

Q: "List all the pins of type INPUT for the macro and2_1 in the high density library."
A: Let's think step by step. In the question "List all the pins of type INPUT for the macro and2_1 in the high density library", we are asked:
"all the pins" so we need table = [Pins]
"of type INPUT" so we need column = [Pins.Direction]
"for the macro for the macro and2_1 in the high density library" so we need table = [Macros] and column = [Macros.Name] and [Macros.Cell_Library]
Based on the columns and tables, we need these Foreign_keys = [Pins.Macro_ID = Macros.Macro_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['INPUT', 'sky130_fd_sc_hd__and2_1', 'sky130_fd_sc_hd'].
So the Schema_links are:
Schema_links: [Pins.*, Pins.Direction, 'INPUT', Pins.Macro_ID = Macros.Macro_ID, Macros.Name, 'sky130_fd_sc_hd__and2_1', Macros.Cell_Library = 'sky130_fd_sc_hd']

Q: "Find all macros with their associated pins that have layers on met1 and met2 in the high speed library."
A: Let's think step by step. In the question "Find all macros with their associated pins that have layers on met1 and met2 in the high speed library.", we are asked:
"all macros" so we need table = [Macros]
"with their associated pins" so we need table = [Pins]
"that have layers on met1 and met2" so we need table = [Pin_Ports] and column = [Pin_Ports.Layer]
"in the high speed library" so we need table [Macros] and column [Cell_Library]
Based on the columns and tables, we need these Foreign_keys = [Pins.Macro_ID = Macros.Macro_ID, Pin_Ports.Pin_ID = Pins.Pin_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['met1', 'met2', 'sky130_fd_sc_hs'].
So the Schema_links are:
Schema_links: [Macros., Pins., Pins.Macro_ID = Macros.Macro_ID, Pin_Ports.Pin_ID = Pins.Pin_ID, Pin_Ports.Layer, 'met1', 'met2', Macros.Cell_Library, 'sky130_fd_sc_hs']

Q: "Find all macros with obstructions on the met4 layer in the high density library."
A: Let's think step by step. In the question "Find all macros with obstructions on the met4 layer in the sky130_fd_sc_hd library.", we are asked:
"all macros" so we need table = [Macros]
"with obstructions" so we need table = [Obstructions]
"on the met4 layer" so we need column = [Obstructions.Layer]
"in the high density library" so we need column = [Macros.Cell_Library]
Based on the columns and tables, we need these Foreign_keys = [Obstructions.Macro_ID = Macros.Macro_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['met4', 'sky130_fd_sc_hd'].
So the Schema_links are:
Schema_links: [Macros.*, Obstructions.*, Obstructions.Macro_ID = Macros.Macro_ID, Obstructions.Layer, 'met4', Macros.Cell_Library, 'sky130_fd_sc_hd']

Q: "Which macro in the medium speed library has the largest total antenna diff area?"
A: Let's think step by step. In the question "Which macro in the sky130_fd_sc_ms library has the largest total antenna diff area?", we are asked:
"Which macro" so we need table = [Macros]
"in the medium speed library" so we need column = [Macros.Cell_Library]
"has the largest total antenna diff area" so we need table = [Pins] and sum [Pins.Antenna_Diff_Area]
Based on the columns and tables, we need these Foreign_keys = [Pins.Macro_ID = Macros.Macro_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['sky130_fd_sc_ms'].
So the Schema_links are:
Schema_links: [Macros.*, Pins.*, Pins.Macro_ID = Macros.Macro_ID, Pins.Antenna_Diff_Area, Macros.Cell_Library, 'sky130_fd_sc_ms']

Schema of the Liberty database with sample rows and column descriptions:
#

{lib_table_info}
{lib_table_descr}


Foreign Keys:
{lib_fk_str}

Q: "What are all the cells with leakage power greater than 3.0 ?"
A: Let's think step by step. In the question "What are all the cells with leakage power greater than 3.0", we are asked:
"all the cells" so we need table = [Cells]
"with leakage power greater than 3.0" so we need column = [Cells.Leakage_Power]
we need table = [Operating_Conditions] and column = [Operating_Conditions.Temperature, Operating_Conditions.Voltage] in order to filter the entries with the correct operating conditions
Based on the columns and tables, we need these Foreign_keys = [Cells.Condition_ID = Operating_Conditions.Condition_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [3.0, '25.0', '1.8'].
So the Schema_links are:
Schema_links: [Cells.*, Cells.Leakage_Power, 3.0, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, '25', Operating_Conditions.Voltage, '1.8']

Q: "Which cells have input pins with clock functionality and what is their capacitance?"
A: Let's think step by step. In the question "Which cells have input pins with clock functionality and what is their capacitance?", we are asked:
"Which cells" so we need table = [Cells]
"have input pins with clock functionality" so we need table = [Input_Pins] and column = [Input_Pins.Clock]
"what is their capacitance" so we need column = [Input_Pins.Capacitance]
we need table = [Operating_Conditions] and column = [Operating_Conditions.Temperature, Operating_Conditions.Voltage] in order to filter the entries with the correct operating conditions
Based on the columns and tables, we need these Foreign_keys = [Input_Pins.Cell_ID = Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [True, 25.0, 1.8].
So the Schema_links are:
Schema_links: [Cells.*, Input_Pins.Cell_ID = Cells.Cell_ID, Input_Pins.Clock, True, Input_Pins.Capacitance, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, '25', Operating_Conditions.Voltage, '1.8']

Q: "Which cells have output pin capacitance greater than 0.2?"
A: Let's think step by step. In the question "Which cells have output pin capacitance greater than 0.2?", we are asked:
- "Which cells" so we need table = [Cells]
- "have output pin capacitance greater than 0.2" so we need table = [Output_Pins] and column = [Output_Pins.Max_Capacitance]
- We need table = [Operating_Conditions] and column = [Operating_Conditions.Temperature, Operating_Conditions.Voltage] in order to filter the entries with the correct operating conditions
Based on the columns and tables, we need these **Foreign_keys** = [Output_Pins.Cell_ID = Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID].
Based on the tables, columns, and Foreign_keys, the **set of possible cell values** are = [0.2, '25.0', '1.8'].
So the **Schema_links** are:
Schema_links: [Cells.*, Output_Pins.Cell_ID = Cells.Cell_ID, Output_Pins.Max_Capacitance, 0.2, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, '25', Operating_Conditions.Voltage, '1.8']


Q: "Which cells have an input pin with a transition delay greater than 0.5?"
A: Let's think step by step. In the question "Which cells have an input pin with a transition delay greater than 0.5?", we are asked:
- "Which cells" so we need table = [Cells]
- "have an input pin with a transition delay greater than 0.5" so we need table = [Timing_Values] and column = [Timing_Values.Input_Transition]
- We need table = [Operating_Conditions] and column = [Operating_Conditions.Temperature, Operating_Conditions.Voltage] in order to filter the entries with the correct operating conditions
Based on the columns and tables, we need these **Foreign_keys** = [Timing_Values.Cell_ID = Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID].
Based on the tables, columns, and Foreign_keys, the **set of possible cell values** are = [0.5, '25.0', '1.8'].
So the **Schema_links** are:
Schema_links: [Cells.*, Timing_Values.Cell_ID = Cells.Cell_ID, Timing_Values.Input_Transition, 0.5, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, '25', Operating_Conditions.Voltage, '1.8']

Q: "Which cells have the largest difference between rise and fall delay for an output pin?"
A: Let's think step by step. In the question "Which cells have the largest difference between rise and fall delay for an output pin?", we are asked:
- "Which cells" so we need table = [Cells]
- "largest difference between rise and fall delay" so we need table = [Timing_Values] and columns = [Timing_Values.Rise_Delay, Timing_Values.Fall_Delay]
- We need table = [Operating_Conditions] and column = [Operating_Conditions.Temperature, Operating_Conditions.Voltage] in order to filter the entries with the correct operating conditions
Based on the columns and tables, we need these **Foreign_keys** = [Timing_Values.Cell_ID = Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID].
Based on the tables, columns, and Foreign_keys, the **set of possible cell values** are = ['25.0', '1.8'].
So the **Schema_links** are:
Schema_links: [Cells.*, Timing_Values.Cell_ID = Cells.Cell_ID, Timing_Values.Rise_Delay, Timing_Values.Fall_Delay, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, '25', Operating_Conditions.Voltage, '1.8']


Technology LEF Schema Tables:
{tlef_table_info}
{tlef_table_descr}

Foreign Keys:
{tlef_fk_str}


Q: "Find all routing layers with horizontal direction that have resistance per square greater than 10 in the high density library."
A: Let's think step by step. In the question "Find all routing layers with horizontal direction that have resistance per square greater than 10 in the sky130_fd_sc_hd library.", we are asked:
"all routing layers" so we need table = [Routing_Layers]
"with horizontal direction" so we need column = [Routing_Layers.Direction]
"that have resistance per square greater than 10" so we need column = [Routing_Layers.Resistance_Per_SQ]
"in the high density library" so we need column = [Routing_Layers.Cell_Library]
The user didn't specify the corner, but we will default it to the nom corner so we need column = [Routing_Layers.Corner]
Based on the columns and tables, we need these Foreign_keys = [].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['HORIZONTAL', 10, 'sky130_fd_sc_hd', 'nom'].
So the Schema_links are:
Schema_links: [Routing_Layers.*, Routing_Layers.Direction, 'HORIZONTAL', Routing_Layers.Resistance_Per_SQ, 10, Routing_Layers.Cell_Library, 'sky130_fd_sc_hd', Routing_Layers.Corner, 'nom']

Q: "Find all routing layers with a minimum width less than 0.15 in the high density library."
A: Let's think step by step. In the question "Find all routing layers with a minimum width less than 0.15 in the sky130_fd_sc_hd library.", we are asked:
"all routing layers" so we need table = [Routing_Layers]
"with a minimum width less than 0.15" so we need column = [Routing_Layers.Min_Width]
"in the high density library" so we need column = [Routing_Layers.Cell_Library]
The user didn't specify the corner, but we will default it to the nom corner so we need column = [Routing_Layers.Corner]
Based on the columns and tables, we need these Foreign_keys = [].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [0.15, 'sky130_fd_sc_hd', 'nom'].
So the Schema_links are:
Schema_links: [Routing_Layers.*, Routing_Layers.Min_Width, 0.15, Routing_Layers.Cell_Library, 'sky130_fd_sc_hd', Routing_Layers.Corner, 'nom']


Q: "Find all cut layers that have a resistance greater than 5 in the nominal corner."
A: Let's think step by step. In the question "Find all cut layers that have a resistance greater than 5 in the nominal corner.", we are asked:
"all cut layers" so we need table = [Cut_Layers]
"that have a resistance greater than 5" so we need column = [Cut_Layers.Resistance]
"in the nominal corner" so we need column = [Cut_Layers.Corner]
The user didn't specify the cell library, so we will default it to the high density library so we need column = [Cut_Layers.Cell_Library]
Based on the columns and tables, we need these Foreign_keys = [].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [5, 'sky130_fd_sc_hd', 'nom'].
So the Schema_links are:
Schema_links: [Cut_Layers.*, Cut_Layers.Resistance, 5, Cut_Layers.Cell_Library, 'sky130_fd_sc_hd', Cut_Layers.Corner, 'nom']

Q: "Find all metal layers in the high density library with pitch values greater than 2.0."
A: Let's think step by step. In the question "Find all metal layers in the sky130_fd_sc_hd library with pitch values greater than 2.0.", we are asked:
"all metal layers" so we need table = [Routing_Layers]
"with pitch values greater than 2.0" so we need column = [Routing_Layers.Pitch_X]
"in the high density library" so we need column = [Routing_Layers.Cell_Library]
The user didn't specify the corner, but we will default it to the nom corner so we need column = [Routing_Layers.Corner]
Based on the columns and tables, we need these Foreign_keys = [].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [2.0, 'sky130_fd_sc_hd', 'nom'].
So the Schema_links are:
Schema_links: [Routing_Layers.*, Routing_Layers.Pitch_X, 2.0, Routing_Layers.Cell_Library, 'sky130_fd_sc_hd', Routing_Layers.Corner, 'nom']

Q: "Find the names of all vias that have a lower metal layer set to met2."
A: Let's think step by step. In the question "Find the names of all vias that have a lower metal layer set to met2.", we are asked:
"all vias" so we need table = [Vias]
"that have a lower metal layer set to met2" so we need column = [Vias.Lower_Layer]
The question didn't specify corner, so we will default it to the nom corner, so we need column = [Vias.Corner]
The user didn't specify the cell library, so we will default it to the high density library so we need column = [Vias.Cell_Library]
Based on the columns and tables, we need these Foreign_keys = [].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = ['met2', 'sky130_fd_sc_hd', 'nom'].
So the Schema_links are:
Schema_links: [Vias.*, Vias.Lower_Layer, 'met2', Vias.Cell_Library, 'sky130_fd_sc_hd', Vias.Corner, 'nom']
"""


##### Cypher SCHEMA LINKERS ########
CYPHER_SCHEMA_LINKERS = lambda node_descr, relationship_descr: f"""
You are an agent designed to find the schema_links for generating Cypher queries for each question based on the graph database schema and relationships.
The schema_links should include the relevant nodes, attributes, and their relationships needed to answer the question.

###
Here is the schema of the Physical Design graph database with node descriptions:
###

{node_descr}

Relationships:
{relationship_descr}

###
Few examples of this task are:
###

Q: "Find all cells with cell_name starting with 'sky130_fd_sc_hd__buf' that are buffers."
A: Let's think step by step. In the question "Find all cells with cell_name starting with 'sky130_fd_sc_hd__buf' that are buffers", we are asked:
"all cells" so we need node = [Cell]
"with cell_name starting with 'sky130_fd_sc_hd__buf'" so we need attribute = [Cell.cell_name]
"that are buffers" so we need attribute = [Cell.is_buf]
Based on the nodes, attributes, and relationships, The set of possible property values are = ['sky130_fd_sc_hd__buf%', true].
So the Schema_links are:
Schema_links: [Cell, Cell.cell_name, 'sky130_fd_sc_hd__buf%', Cell.is_buf, true]

Q: "What are the nets connected to cell instance '_24_' and their total capacitance?"
A: Let's think step by step. In the question "What are the nets connected to cell instance '_24_' and their total capacitance?", we are asked:
"the nets" so we need node = [Net]
"connected to cell instance '_24_'" so we need node = [Cell] and attribute = [Cell.instance_name]
"and their total capacitance" so we need attribute = [Net.total_cap]
Based on the nodes, attributes, and relationships, we need this relationship = [(:Cell)-[:CONNECTS_TO]->(:Net)].
Based on the nodes, attributes, and relationships, The set of possible property values are = ['_24_'].
So the Schema_links are:
Schema_links: [Cell, Cell.instance_name, '_24_', Cell-[:CONNECTS_TO]->Net, Net, Net.total_cap]

Q: "Find all input ports on the left boundary of the design that have signal type 'SIGNAL'."
A: Let's think step by step. In the question "Find all input ports on the left boundary of the design that have signal type 'SIGNAL'", we are asked:
"all input ports" so we need node = [Port] and attribute = [Port.direction]
"on the left boundary of the design" so we need relationship = [(:Design)-[:HAS_PORT]->(:Port)] and attributes = [Port.x, Design.xmin]
"that have signal type 'SIGNAL'" so we need attribute = [Port.signal_type]
Based on the nodes, attributes, and relationships, we need this relationship = [(:Design)-[:HAS_PORT]->(:Port)].
Based on the nodes, attributes, and relationships, The set of possible property values are = ['INPUT', 'SIGNAL'].
So the Schema_links are:
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.direction, 'INPUT', Port.x, Design.xmin, Port.signal_type, 'SIGNAL']

Q: "Which cells drive nets with high fanout (more than 10) and what is their power consumption?"
A: Let's think step by step. In the question "Which cells drive nets with high fanout (more than 10) and what is their power consumption?", we are asked:
"Which cells" so we need node = [Cell]
"drive nets" so we need relationship = [(:Cell)-[:CONNECTS_TO]->(:Net)]
"with high fanout (more than 10)" so we need node = [Net] and attribute = [Net.fanout]
"what is their power consumption" so we need attributes = [Cell.static_power, Cell.dynamic_power]
Based on the nodes, attributes, and relationships, we need this relationship = [(:Cell)-[:CONNECTS_TO]->(:Net)].
Based on the nodes, attributes, and relationships, The set of possible property values are = [10].
So the Schema_links are:
Schema_links: [Cell, Cell-[:CONNECTS_TO]->Net, Net.fanout, 10, Cell.static_power, Cell.dynamic_power]

Q: "Find all sequential cells in the clock network and their locations."
A: Let's think step by step. In the question "Find all sequential cells in the clock network and their locations", we are asked:
"all sequential cells" so we need node = [Cell] and attribute = [Cell.is_seq]
"in the clock network" so we need attribute = [Cell.is_in_clk]
"and their locations" so we need attributes = [Cell.x0, Cell.y0]
Based on the nodes, attributes, and relationships, The set of possible property values are = [true, true].
So the Schema_links are:
Schema_links: [Cell, Cell.is_seq, true, Cell.is_in_clk, true, Cell.x0, Cell.y0]

Q: "What are the nets routed on metal layer 'met3' and their total routed length?"
A: Let's think step by step. In the question "What are the nets routed on metal layer 'met3' and their total routed length?", we are asked:
"What are the nets" so we need node = [Net]
"routed on metal layer 'met3'" so we need node = [Segment] with attribute = [Segment.layer] and relationship = [(:Net)-[:ROUTED_ON]->(:Segment)]
"and their total routed length" so we need attribute = [Net.routed_length]
Based on the nodes, attributes, and relationships, we need this relationship = [(:Net)-[:ROUTED_ON]->(:Segment)].
Based on the nodes, attributes, and relationships, The set of possible property values are = ['met3'].
So the Schema_links are:
Schema_links: [Net, Net-[:ROUTED_ON]->Segment, Segment.layer, 'met3', Net.routed_length]

Q: "Find all cell pins with negative slack and their corresponding cells."
A: Let's think step by step. In the question "Find all cell pins with negative slack and their corresponding cells", we are asked:
"all cell pins" so we need node = [CellInternalPin]
"with negative slack" so we need attribute = [CellInternalPin.pin_slack]
"and their corresponding cells" so we need node = [Cell] and relationship = [(:CellInternalPin)-[:BELONGS_TO]->(:Cell)]
Based on the nodes, attributes, and relationships, we need this relationship = [(:CellInternalPin)-[:BELONGS_TO]->(:Cell)].
Based on the nodes, attributes, and relationships, The set of possible property values are = [0].
So the Schema_links are:
Schema_links: [CellInternalPin, CellInternalPin.pin_slack, 0, CellInternalPin-[:BELONGS_TO]->Cell, Cell]
"""

#### SQL Classifier #####
QUERY_CLASSIFIER_SYS_PROMPT =  lambda lef_table_info, lef_table_descr, lef_fk_str, tlef_table_info, tlef_table_descr, tlef_fk_str, lib_table_info, lib_table_descr, lib_fk_str: f"""
For the given question, classify it as EASY, NON-NESTED, or NESTED based on nested queries and JOIN.
if need nested queries: predict NESTED
elif need JOIN and don't need nested queries: predict NON-NESTED
elif don't need JOIN and don't need nested queries: predict EASY
Note: Don't mistake the WHERE conditions with nested queries.
Note: Only predict NESTED if the question needs nested queries, if it can be solved with JOIN, predict NON-NESTED.
###
Few examples of this task are:
###
Schema of the LEF database with sample rows and column descriptions:
##

{lef_table_info}
{tlef_table_info}
{lib_table_info}

{lef_table_descr}
{tlef_table_descr}
{lib_table_descr}

Foreign_keys:
{lef_fk_str}
{tlef_fk_str}
{lib_fk_str}

""" + """
Q: "Find all macros in the Macros table which have Size_Width greater than 1.2."
schema_links: [Macros.Name, Macros.Size_Width, 1.2, Macros.Cell_Library, 'sky130_fd_sc_hd']
A: "Let’s think step by step. This query needs only the Macros table with a simple condition (Size_Width > 1.2). No JOIN or nested query is required, so it is classified as 'EASY'."
Label: 
```json 
{{
    "label": "EASY"
}}
```

Q: "Which macros in the Macros table have a Size_Height larger than 2.0?"
schema_links: [Macros.Name, Macros.Size_Height, 2.0, Macros.Cell_Library, 'sky130_fd_sc_hd']
A: "Let’s think step by step. This query uses only the Macros table (no JOIN needed) and a simple condition (Size_Height > 2.0). No nesting is required, so it is classified as 'EASY'."
Label: 
```json 
{{
    "label": "EASY"
}}
```

Q: "Find all macros (from Macros) that appear in the Pins table with Direction = 'OUTPUT', and list their Size_Width from the Macros table."
schema_links: [Macros.Macro_ID = Pins.Macro_ID, Pins.Direction, 'OUTPUT', Macros.Size_Width, Macros.Cell_Library, 'sky130_fd_sc_hd']
A: "Let’s think step by step. We need a JOIN between Macros and Pins on Macro_ID, then filter by Pins.Direction = 'OUTPUT' and show Macros.Size_Width. No nested query is required, so it is 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```


Q: "For each cell in the Cells table, find the names of input pins in Input_Pins whose Capacitance is larger than the average Capacitance of all input pins in that same cell."
schema_links: [Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8, Input_Pins.Cell_ID = Cells.Cell_ID, Input_Pins.Input_Pin_Name, Input_Pins.Capacitance, AVG(Input_Pins.Capacitance)]
A: "Let's think step by step. We compare each Input_Pin's Capacitance to the average Capacitance for that cell under standard operating conditions. For example: WHERE Input_Pins.Capacitance > (SELECT AVG(p2.Capacitance) FROM Input_Pins p2 JOIN Cells c2 ON p2.Cell_ID = c2.Cell_ID JOIN Operating_Conditions oc2 ON c2.Condition_ID = oc2.Condition_ID WHERE p2.Cell_ID = Input_Pins.Cell_ID AND oc2.Temperature = 25.0 AND oc2.Voltage = 1.8). Because of this subselect, it is 'NESTED'."
Label: 
```json 
{{
    "label": "NESTED"
}}
```

Q: "Which input pins in the Input_Pins table have Clock = True and appear in the Cells table with an Area over 20.0 under standard operating conditions, ordered by the Cells.Area descending?"
schema_links: [Input_Pins.Cell_ID = Cells.Cell_ID, Input_Pins.Clock, True, Cells.Area, 20.0, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: "Let's think step by step. We need a JOIN on Cell_ID between Input_Pins and Cells, a JOIN between Cells and Operating_Conditions on Condition_ID, filter for Clock = True, Cells.Area > 20.0, Operating_Conditions.Temperature = 25.0, and Operating_Conditions.Voltage = 1.8, then sort by Cells.Area in descending order. No nested query, so it is 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```


Q: "Give me the total number of pins (from the Pins table) for each macro (from the Macros table)."
schema_links: [Macros.Macro_ID = Pins.Macro_ID, COUNT(Pins.Pin_ID), GROUP BY Macros.Macro_ID]
A: "Let’s think step by step. We need a JOIN on Macro_ID between Macros and Pins, then GROUP BY Macros.Macro_ID (or Macros.Name) to count how many Pins each macro has. No nested query is required, so it is 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "List the names of macros in the Macros table that do not have any references in the Pins table." 
schema_links: [Macros.Macro_ID, Pins.Macro_ID, NOT IN]
A: "Let’s think step by step. We can use a subselect, for example: WHERE Macros.Macro_ID NOT IN ( SELECT Pins.Macro_ID FROM Pins ). Because of this subselect, the query is 'NESTED'." 
Label: 
```json 
{{
    "label":  "NESTED"
}}
```

Q: "Find the names of macros in the Macros table whose Size_Width is less than the average Size_Width of all macros in the Macros table." 
schema_links: [Macros.Name, Macros.Size_Width, AVG(Macros.Size_Width)] 
A: "Let’s think step by step. We compare each macro's Size_Width to the overall average using a subselect: WHERE Macros.Size_Width < ( SELECT AVG(m2.Size_Width) FROM Macros m2 ). Because of the subselect, it is 'NESTED'." 
Label:
```json 
{{
    "label":  "NESTED"
}}
```

Q: "Which macros in the Macros table have more than 5 pins in total, referencing the Pins table?"
schema_links: [Macros.Macro_ID = Pins.Macro_ID, COUNT(Pins.Pin_ID), GROUP BY, HAVING]
A: "Let’s think step by step. We can JOIN Macros and Pins on Macro_ID, GROUP BY Macros.Macro_ID, then use HAVING COUNT(Pins.Pin_ID) > 5. This is done via a JOIN and a GROUP BY, with no nested query needed, so it is 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

[Instructions]
    - You must output your answer in the same format as the given examples.
    - Give an explaination first of your classification then output the label in the following json format: 
    ```json 
        {{
        "label": <predicted-label>
        }}
    ```
""" 

######## Cypher Query Classifier ##########
CYPHER_QUERY_CLASSIFIER_SYS_PROMPT = lambda node_descr, relationship_descr: f"""
For the given question, classify it as EASY, NON-NESTED, or NESTED based on query complexity.
if need subqueries or advanced pattern matching: predict NESTED
elif need multiple node pattern matching or aggregations: predict NON-NESTED
elif only need simple node pattern matching: predict EASY
Note: Don't mistake WHERE conditions with subqueries.
Note: Only predict NESTED if the question needs subqueries, if it can be solved with simple pattern matching and aggregations, predict NON-NESTED.
###
Here is the schema of the Physical Design graph database with node descriptions:
###

{node_descr}

Relationships:
{relationship_descr}
""" + """
###
Few examples of this task are:
###

Q: "Find all cells with cell_name starting with 'sky130_fd_sc_hd__buf'."
schema_links: [Cell, Cell.cell_name, 'sky130_fd_sc_hd__buf%']
A: "Let's think step by step. This query needs only to match Cell nodes with a property filter (cell_name STARTS WITH 'sky130_fd_sc_hd__buf'). No complex pattern matching or aggregations are required, so it is classified as 'EASY'."
Label: 
```json 
{{
    "label": "EASY"
}}
```

Q: "What is the total number of cells in the design?"
schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, COUNT(Cell)]
A: "Let's think step by step. This query requires matching Design nodes and their CONTAINS_CELL relationships to Cell nodes, then counting the total. It needs a simple pattern match with aggregation (COUNT), but no subqueries, so it is classified as 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "Find all cells and their connected nets."
schema_links: [Cell, Cell-[:CONNECTS_TO]->Net, Net]
A: "Let's think step by step. This query requires matching Cell nodes, following their CONNECTS_TO relationships to Net nodes. It involves a simple pattern match across multiple node types, but no aggregations or subqueries, so it is classified as 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "Find cells that have more pins than the average number of pins per cell."
schema_links: [Cell, Cell-[:HAS_PIN]->CellInternalPin, COUNT(CellInternalPin), AVG(COUNT(CellInternalPin))]
A: "Let's think step by step. This query requires first calculating the average number of pins across all cells as a subquery, then finding cells that have more pins than this average. This requires a nested query structure in Cypher, so it is classified as 'NESTED'."
Label: 
```json 
{{
    "label": "NESTED"
}}
```

Q: "List cells that are connected to nets with fanout greater than 10."
schema_links: [Cell, Cell-[:CONNECTS_TO]->Net, Net.fanout, 10]
A: "Let's think step by step. This query requires matching Cell nodes that connect to Net nodes with a fanout property greater than 10. It involves a simple pattern match with a property filter, but no aggregations or subqueries, so it is classified as 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "Find cells that don't have any pins."
schema_links: [Cell, NOT Cell-[:HAS_PIN]->CellInternalPin]
A: "Let's think step by step. This query requires finding Cell nodes that do not have any HAS_PIN relationships to CellInternalPin nodes. In Cypher, this requires a negation pattern which is equivalent to a subquery, so it is classified as 'NESTED'."
Label: 
```json 
{{
    "label": "NESTED"
}}
```

Q: "For each cell, find the maximum pin_slack of its pins."
schema_links: [Cell, Cell-[:HAS_PIN]->CellInternalPin, MAX(CellInternalPin.pin_slack)]
A: "Let's think step by step. This query requires matching Cell nodes, their HAS_PIN relationships to CellInternalPin nodes, then grouping by Cell and calculating the maximum pin_slack. It involves pattern matching with aggregation (MAX), but no subqueries, so it is classified as 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "Find cells that have at least one pin with negative slack and at least one pin with positive slack."
schema_links: [Cell, Cell-[:HAS_PIN]->CellInternalPin, CellInternalPin.pin_slack, <0, >0]
A: "Let's think step by step. This query requires finding Cell nodes that have both: 1) HAS_PIN relationships to CellInternalPin nodes with pin_slack < 0, and 2) HAS_PIN relationships to CellInternalPin nodes with pin_slack > 0. In Cypher, this requires multiple pattern matches combined, which is equivalent to a subquery structure, so it is classified as 'NESTED'."
Label: 
```json 
{{
    "label": "NESTED"
}}
```

Q: "Count the number of cells for each cell_name."
schema_links: [Cell, Cell.cell_name, COUNT(Cell), GROUP BY Cell.cell_name]
A: "Let's think step by step. This query requires matching Cell nodes, grouping them by cell_name, and counting the occurrences. It involves a simple pattern match with grouping and aggregation (COUNT), but no subqueries, so it is classified as 'NON-NESTED'."
Label: 
```json 
{{
    "label": "NON-NESTED"
}}
```

Q: "Find all ports on the design's left boundary."
schema_links: [Design, Design-[:HAS_PORT]->Port, Port.x, Design.xmin]
A: "Let's think step by step. This query requires matching Design nodes, following their HAS_PORT relationships to Port nodes, and filtering for ports where x = Design.xmin. It involves simple pattern matching with property comparison, but no subqueries or complex aggregations, so it is classified as 'EASY'."
Label: 
```json 
{{
    "label": "EASY"
}}
```

Q: "Find the cell with the highest dynamic power consumption."
schema_links: [Cell, Cell.dynamic_power, ORDER BY, LIMIT]
A: "Let's think step by step. This query requires matching Cell nodes, ordering them by dynamic_power in descending order, and limiting to the first result. It involves a simple pattern match with ordering and limiting, but no complex pattern matching, aggregations, or subqueries, so it is classified as 'EASY'."
Label: 
```json 
{{
    "label": "EASY"
}}
```

Q: "Find cells that are connected to nets that are not connected to any port."
schema_links: [Cell, Cell-[:CONNECTS_TO]->Net, NOT Net-[:CONNECTS_TO]->Port]
A: "Let's think step by step. This query requires finding Cell nodes that connect to Net nodes that do not have any CONNECTS_TO relationships to Port nodes. In Cypher, this requires a negation pattern which is equivalent to a subquery, so it is classified as 'NESTED'."
Label: 
```json 
{{
    "label": "NESTED"
}}
```

[Instructions]
    - You must output your answer in the same format as the given examples.
    - Give an explanation first of your classification then output the label in the following json format: 
    ```json 
        {{
        "label": <predicted-label>
        }}
    ```
"""

#### SQL Generator #####

EASY_SYS_PROMPT =  lambda lef_table_info, lef_table_descr, lef_fk_str, tlef_table_info, tlef_table_descr, tlef_fk_str, lib_table_info, lib_table_descr, lib_fk_str: f"""
Use the schema links to generate the correct sqlite SQL query for the given question.

{lef_table_info}
{tlef_table_info}
{lib_table_info}

{lef_table_descr}
{tlef_table_descr}
{lib_table_descr}

Foreign_keys:
{lef_fk_str}
{tlef_fk_str}
{lib_fk_str}

Q: "Find all macros with width greater than 2.0 from the high density library."
Schema_links: [Macros.Name, Macros.Size_Width, 2.0, Macros.Cell_Library, sky130_fd_sc_hd]
SQL: 
```sql
SELECT Name FROM Macros WHERE Size_Width > 2.0 AND Cell_Library = 'sky130_fd_sc_hd'
```

Q: "List all input pins for the macro and2_1 cell in the high density library."
Schema_links: [Pins.Name,Pins.Direction,INPUT,Pins.Macro_ID,Macros.Macro_ID,Macros.Name,sky130_fd_sc_hd__and2_1]
SQL: 
```sql
SELECT Pins.Name FROM Pins JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Pins.Direction = 'INPUT' AND Macros.Name = 'sky130_fd_sc_hd__and2_1'
```

Q: "Find the average leakage power of all cells in the high density library."
Schema_links: [Cells.Leakage_Power,Cells.Condition_ID,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library,sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
SQL: 
```sql
SELECT AVG(Cells.Leakage_Power) FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8
```

Q: "Count how many cells have buffers in each library."
Schema_links: [Cells.Cell_ID,Cells.Is_Buffer,TRUE,Cells.Condition_ID,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
SQL: 
```sql
SELECT Operating_Conditions.Cell_Library, COUNT(Cells.Cell_ID) FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Is_Buffer = TRUE AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8  GROUP BY Operating_Conditions.Cell_Library
```

Q: "List all routing layers with resistance per square greater than 10 in descending order of resistance."
Schema_links: [Routing_Layers.Name,Routing_Layers.Resistance_Per_SQ,10]
SQL: 
```sql
SELECT Name, Resistance_Per_SQ FROM Routing_Layers WHERE Resistance_Per_SQ > 10 ORDER BY Resistance_Per_SQ DESC
```

Q: "Find the average capacitance of input pins across all cells that are flip-flops."
Schema_links: [Input_Pins.Capacitance,Input_Pins.Cell_ID,Cells.Cell_ID,Cells.Is_Flip_Flop,TRUE,Operating_Conditions.Cell_Library, sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
SQL: 
```sql
SELECT AVG(Input_Pins.Capacitance) FROM Input_Pins JOIN Cells ON Input_Pins.Cell_ID = Cells.Cell_ID JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Is_Flip_Flop = TRUE AND Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8
```

Q: "List all macros with their height and width that have pins used for power in the medium speed library."
Schema_links: [Macros.Name,Macros.Size_Height,Macros.Size_Width,Macros.Macro_ID,Pins.Macro_ID,Pins.Use,POWER, Macros.Cell_Library, sky130_fd_sc_ms]
SQL: 
```sql
SELECT DISTINCT Macros.Name, Macros.Size_Height, Macros.Size_Width FROM Macros JOIN Pins ON Macros.Macro_ID = Pins.Macro_ID WHERE Pins.Use = 'POWER' AND Macros.Cell_Library = 'sky130_fd_sc_ms'
```

Q: "Find all cells that have both an area greater than 15 and leakage power less than 3 in the high density low leakage library."
Schema_links: [Cells.Name,Cells.Area,15,Cells.Leakage_Power,3,Operating_Conditions.Cell_Library, sky130_fd_sc_hdll, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
SQL: 
```sql
SELECT Cells.Name FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Area > 15 AND Cells.Leakage_Power < 3 AND Operating_Conditions.Cell_Library = 'sky130_fd_sc_hdll' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8

Q: "Count the number of pins for each direction type across all macros in the low speed library."
Schema_links: [Pins.Direction,Pins.Pin_ID, Macros.Macro_ID, Macros.Cell_Library, sky130_fd_sc_ls]
SQL: 
```sql
SELECT Pins.Direction, COUNT(Pins.Pin_ID) FROM Pins JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_ls' GROUP BY Pins.Direction
```

Q: "Find the cell with the highest maximum output pin capacitance."
Schema_links: [Cells.Name,Cells.Cell_ID,Output_Pins.Cell_ID,Output_Pins.Max_Capacitance, Operating_Conditions.Condition_ID, Operating_Conditions.Temperature, 25.0,Operating_Conditions.Voltage, 1.8]
SQL: 
```sql
SELECT Cells.Name FROM Cells JOIN Output_Pins ON Cells.Cell_ID = Output_Pins.Cell_ID JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8 ORDER BY Output_Pins.Max_Capacitance DESC LIMIT 1

Q: "List all vias connecting metal1 and metal2 layers."
Schema_links: [Vias.Name,Vias.Lower_Layer,met1,Vias.Upper_Layer,met2, Vias.Cell_Library, 'sky130_fd_sc_hd', Vias.Corner, 'nom']
SQL: 
```sql
SELECT Name FROM Vias WHERE Lower_Layer = 'met1' AND Upper_Layer = 'met2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'
```

Q: "Calculate the average width of all horizontal routing layers."
Schema_links: [Routing_Layers.Width,Routing_Layers.Direction,HORIZONTAL, Routing_Layers.Cell_Library, 'sky130_fd_sc_hd', Routing_Layers.Corner = 'nom']
SQL: 
```sql
SELECT AVG(Width) FROM Routing_Layers WHERE Direction = 'HORIZONTAL' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'
```

[Instructions]
- You must output your answer in the same format as the given examples.

"""

NON_NESTED_SYS_PROPMT = lambda lef_table_info, lef_table_descr, lef_fk_str, tlef_table_info, tlef_table_descr, tlef_fk_str, lib_table_info, lib_table_descr, lib_fk_str: f"""
# Use the schema links and Intermediate_representation to generate the SQL queries for each of the questions.

{lef_table_info}
{tlef_table_info}
{lib_table_info}

{lef_table_descr}
{tlef_table_descr}
{lib_table_descr}

Foreign_keys:
{lef_fk_str}
{tlef_fk_str}
{lib_fk_str}

Q: "Find all macros with width greater than 2.0 from the high density library."
Schema_links: [Macros.Name,Macros.Size_Width,2.0,Macros.Cell_Library,sky130_fd_sc_hd]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Macros.Name from Macros where Macros.Size_Width > 2.0 and Macros.Cell_Library = "sky130_fd_sc_hd"
SQL: 
```sql
SELECT Name FROM Macros WHERE Size_Width > 2.0 AND Cell_Library = 'sky130_fd_sc_hd'
```

Q: "List all input pins for the macro sky130_fd_sc_hd__and2_1."
Schema_links: [Pins.Name,Pins.Direction,INPUT,Pins.Macro_ID,Macros.Macro_ID,Macros.Name,sky130_fd_sc_hd__and2_1,Macros.Cell_Library,sky130_fd_sc_hd]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Pins, Macros]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Pins.Name from Pins join Macros on Pins.Macro_ID = Macros.Macro_ID where Pins.Direction = "INPUT" and Macros.Name = "sky130_fd_sc_hd__and2_1" and Macros.Cell_Library = 'sky130_fd_sc_hd'
SQL: 

```sql
SELECT Pins.Name FROM Pins JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Pins.Direction = 'INPUT' AND Macros.Name = 'sky130_fd_sc_hd__and2_1' AND Macros.Cell_Library = 'sky130_fd_sc_hd'
```

Q: "Find the average leakage power of all cells in the sky130_fd_sc_hd library."
Schema_links: [Cells.Leakage_Power,Cells.Condition_ID,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library,sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Cells, Operating_Conditions]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select avg(Cells.Leakage_Power) from Cells join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Operating_Conditions.Cell_Library = "sky130_fd_sc_hd" and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8
SQL: 
```sql
SELECT AVG(Cells.Leakage_Power) FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8
```

Q: "Count how many cells have buffers in each library."
Schema_links: [Cells.Cell_ID,Cells.Is_Buffer,TRUE,Cells.Condition_ID,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Cells, Operating_Conditions]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Operating_Conditions.Cell_Library, count(Cells.Cell_ID) from Cells join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Cells.Is_Buffer = TRUE and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8 group by Operating_Conditions.Cell_Library
SQL: 
```sql
SELECT Operating_Conditions.Cell_Library, COUNT(Cells.Cell_ID) FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Is_Buffer = TRUE AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8 GROUP BY Operating_Conditions.Cell_Library
```

Q: "List all routing layers with resistance per square greater than 10 in descending order of resistance."
Schema_links: [Routing_Layers.Name,Routing_Layers.Resistance_Per_SQ,10,Routing_Layers.Corner,nom,Routing_Layers.Cell_Library,sky130_fd_sc_hd]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Routing_Layers.Name, Routing_Layers.Resistance_Per_SQ from Routing_Layers where Routing_Layers.Resistance_Per_SQ > 10 and Routing_Layers.Corner = 'nom' and Routing_Layers.Cell_Library = 'sky130_fd_sc_hd' order by Routing_Layers.Resistance_Per_SQ desc
SQL: 
```sql
SELECT Name, Resistance_Per_SQ FROM Routing_Layers WHERE Resistance_Per_SQ > 10 AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd' ORDER BY Resistance_Per_SQ DESC
```

Q: "Find the cells with leakage power higher than the average leakage power across all cells in the high density library."
Schema_links: [Cells.Name,Cells.Leakage_Power, Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library, sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Cells.Name from Cells join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Cells.Leakage_Power > (select avg(C.Leakage_Power) from Cells C join Operating_Conditions OC on C.Condition_ID = OC.Condition_ID where OC.Cell_Library = 'sky130_fd_sc_hd' and OC.Temperature = 25.0 and OC.Voltage = 1.8) and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8
SQL: 
```sql
SELECT Cells.Name  FROM Cells JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Leakage_Power > (     SELECT AVG(C.Leakage_Power)      FROM Cells C     JOIN Operating_Conditions OC ON C.Condition_ID = OC.Condition_ID     WHERE OC.Cell_Library = 'sky130_fd_sc_hd' AND OC.Temperature = 25.0     AND OC.Voltage = 1.8 ) AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8
```

Q: "Count the number of pins of each type (INPUT, OUTPUT, INOUT) for each macro in the sky130_fd_sc_hd library."
Schema_links: [Pins.Direction,Pins.Macro_ID,Macros.Macro_ID,Macros.Name,Macros.Cell_Library,sky130_fd_sc_hd]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Pins, Macros]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Macros.Name, Pins.Direction, count(*) from Pins join Macros on Pins.Macro_ID = Macros.Macro_ID where Macros.Cell_Library = "sky130_fd_sc_hd" group by Macros.Name, Pins.Direction
SQL: 

```sql
SELECT Macros.Name, Pins.Direction, COUNT(*) FROM Pins JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hd' GROUP BY Macros.Name, Pins.Direction
```

Q: "Find the total number of macros for each cell library and their average height."
Schema_links: [Macros.Cell_Library,Macros.Macro_ID,Macros.Size_Height]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Macros.Cell_Library, count(Macros.Macro_ID), avg(Macros.Size_Height) from Macros group by Macros.Cell_Library
SQL: 
```sql
SELECT Cell_Library, COUNT(Macro_ID), AVG(Size_Height) FROM Macros GROUP BY Cell_Library
```

Q: "Find all macros that have pins on  met1 layer in the medium speed library."
Schema_links: [Macros.Name,Macros.Macro_ID,Pins.Macro_ID,Pins.Pin_ID,Pin_Ports.Pin_ID,Pin_Ports.Layer,met1, Macros.Cell_Library, sky130_fd_sc_ms]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Macros, Pins, Pin_Ports]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select distinct Macros.Name from Macros join Pins on Macros.Macro_ID = Pins.Macro_ID join Pin_Ports on Pins.Pin_ID = Pin_Ports.Pin_ID where Pin_Ports.Layer = "met1" and Macros.Cell_Library = 'sky130_fd_sc_ms' 
SQL: 
```sql
SELECT DISTINCT Macros.Name  FROM Macros  JOIN Pins ON Macros.Macro_ID = Pins.Macro_ID  JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID  WHERE Pin_Ports.Layer = 'met1'  AND Macros.Cell_Library = 'sky130_fd_sc_ms' 
```

Q: "Find the cell with the highest average delay in the typical operating condition."
Schema_links: [Cells.Name,Cells.Cell_ID,Timing_Values.Cell_ID,Timing_Values.Average_Delay,Cells.Condition_ID,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library,sky130_fd_sc_hd,Operating_Conditions.Temperature,25.0,Operating_Conditions.Voltage,1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Cells, Timing_Values, Operating_Conditions]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Cells.Name, avg(Timing_Values.Average_Delay) as Average_Cell_Delay from Cells join Timing_Values on Cells.Cell_ID = Timing_Values.Cell_ID join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Operating_Conditions.Cell_Library='sky130_fd_sc_hd' and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8 group by Cells.Name order by Average_Cell_Delay desc limit 1
SQL: 
```sql
SELECT Cells.Name, AVG(Timing_Values.Average_Delay) as Average_Cell_Delay FROM Cells  JOIN Timing_Values ON Cells.Cell_ID = Timing_Values.Cell_ID  JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID  WHERE Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' AND Operating_Conditions.Temperature = 25.0  AND Operating_Conditions.Voltage = 1.8 GROUP BY Cells.Name ORDER BY Average_Cell_Delay DESC LIMIT 1
```

Q: "Find all cells that have input pins with clock functionality and their total capacitance is greater than 0.005."
Schema_links: [Cells.Name,Cells.Cell_ID,Input_Pins.Cell_ID,Input_Pins.Clock,TRUE,Input_Pins.Capacitance,0.005,Operating_Conditions.Condition_ID,Operating_Conditions.Cell_Library,sky130_fd_sc_hd,Operating_Conditions.Temperature,25.0,Operating_Conditions.Voltage,1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Cells, Input_Pins]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select distinct Cells.Name from Cells join Input_Pins on Cells.Cell_ID = Input_Pins.Cell_ID join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Input_Pins.Clock = TRUE and Input_Pins.Capacitance > 0.005 and Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8
SQL: 
```sql
SELECT DISTINCT Cells.Name FROM Cells JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Input_Pins.Clock = TRUE  AND Input_Pins.Capacitance > 0.005 AND Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8
```

Q: "Count the number of via definitions between each pair of adjacent metal layers."
Schema_links: [Vias.Lower_Layer,Vias.Upper_Layer,Vias.Via_ID,Vias.Cell_Library,sky130_fd_sc_hd,Vias.Corner,nom]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Vias.Lower_Layer, Vias.Upper_Layer, count(Vias.Via_ID) from Vias where Vias.Cell_Library = 'sky130_fd_sc_hd' and Vias.Corner = 'nom' group by Vias.Lower_Layer, Vias.Upper_Layer
SQL: 
```sql
SELECT Lower_Layer, Upper_Layer, COUNT(Via_ID) FROM Vias WHERE Vias.Cell_Library = 'sky130_fd_sc_hd' AND Vias.Corner = 'nom' GROUP BY Lower_Layer, Upper_Layer 
```

Q: "Find the routing layer with the highest resistance per square in each cell library."
Schema_links: [Routing_Layers.Name,Routing_Layers.Cell_Library,Routing_Layers.Resistance_Per_SQ,Routing_Layers.Corner,nom]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = []. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select Cell_Library, Name, max(Resistance_Per_SQ) as Highest_Resistance from Routing_Layers where Corner = 'nom' and Cell_Library in ('sky130_fd_sc_hs', 'sky130_fd_sc_ms') group by Cell_Library order by Highest_Resistance desc
SQL: 
```sql
SELECT Cell_Library, Name, MAX(Resistance_Per_SQ) as Highest_Resistance FROM Routing_Layers WHERE Corner = 'nom' AND Cell_Library IN ('sky130_fd_sc_hs', 'sky130_fd_sc_ms') GROUP BY Cell_Library ORDER BY Highest_Resistance DESC
```

Q: "Find all cells that have both input pins with clock functionality and output pins with maximum capacitance greater than 0.3 in the high density library."
Schema_links: [Cells.Name,Cells.Cell_ID,Input_Pins.Cell_ID,Input_Pins.Clock,TRUE,Output_Pins.Cell_ID,Output_Pins.Max_Capacitance,0.3,Operating_Conditions.Cell_Library,sky130_fd_sc_hd,Operating_Conditions.Temperature,25.0,Operating_Conditions.Voltage,1.8]
A: Let's think step by step. For creating the SQL for the given question, we need to join these tables = [Cells, Input_Pins, Output_Pins]. First, create an intermediate representation, then use it to construct the SQL query.
Intermediate_representation: select distinct c.Name from Cells c join Input_Pins ip on c.Cell_ID = ip.Cell_ID join Output_Pins op on c.Cell_ID = op.Cell_ID join Operating_Conditions oc on c.Condition_ID = oc.Condition_ID where ip.Clock = TRUE and op.Max_Capacitance > 0.3 and oc.Cell_Library = 'sky130_fd_sc_hd' and oc.Temperature = 25.0 and oc.Voltage = 1.8
SQL: 
```sql
SELECT DISTINCT c.Name  FROM Cells c  JOIN Input_Pins ip ON c.Cell_ID = ip.Cell_ID  JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID  JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE ip.Clock = TRUE  AND op.Max_Capacitance > 0.3 AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
```

[Instructions]
- You must output your answer in the same format as the given examples.

"""

NESTED_COMPLEX_SYS_PROPMT = lambda lef_table_info, lef_table_descr, lef_fk_str, tlef_table_info, tlef_table_descr, tlef_fk_str, lib_table_info, lib_table_descr, lib_fk_str: f"""
# Use the intermediate representation and the schema links to generate the SQL queries for each of the questions.

{lef_table_info}
{tlef_table_info}
{lib_table_info}

{lef_table_descr}
{tlef_table_descr}
{lib_table_descr}

Foreign_keys:
{lef_fk_str}
{tlef_fk_str}
{lib_fk_str}

Q: "Find the macros in the high density library that have exactly two input pins."
Schema_links: [Macros.Name, Macros.Cell_Library, sky130_fd_sc_hd, Macros.Macro_ID = Pins.Macro_ID, Pins.Direction, INPUT]
A: Let's think step by step. "Find the macros in the high density library that have exactly two input pins." can be solved by knowing the answer to the following sub-question "What are the macros in the high density library with exactly two input pins?".
The SQL query for the sub-question "What are the macros in the high density library with exactly two input pins?" is SELECT T1.Name FROM Macros AS T1 JOIN Pins AS T2 ON T1.Macro_ID = T2.Macro_ID WHERE T2.Direction = 'INPUT' AND T1.Cell_Library = 'sky130_fd_sc_hd' GROUP BY T1.Macro_ID HAVING count() = 2
So, the answer to the question "Find the macros in the high density library that have exactly two input pins." is =
Intermediate_representation: select Macros.Name from Macros join Pins on Macros.Macro_ID = Pins.Macro_ID where Pins.Direction = "INPUT" and Macros.Cell_Library = "sky130_fd_sc_hd" group by Macros.Macro_ID having count(Pins.Pin_ID) = 2
SQL:
```sql
SELECT T1.Name FROM Macros AS T1 JOIN Pins AS T2 ON T1.Macro_ID = T2.Macro_ID WHERE T2.Direction = 'INPUT' AND T1.Cell_Library = 'sky130_fd_sc_hd' GROUP BY T1.Macro_ID HAVING count() = 2
```

Q: "Find the name and cell library of the macro with the highest width in the high density low leakage library."
Schema_links: [Macros.Name, Macros.Cell_Library, sky130_fd_sc_hdll, Macros.Size_Width]
A: Let's think step by step. "Find the name and cell library of the macro with the highest width in the high density low leakage library." can be solved by knowing the answer to the following sub-question "What is the macro in the high density low leakage library with the greatest width?".
The SQL query for the sub-question "What is the macro in the high density low leakage library with the greatest width?" is SELECT Name, Cell_Library FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll' ORDER BY Size_Width DESC LIMIT 1
So, the answer to the question "Find the name and cell library of the macro with the highest width in the high density low leakage library." is =
Intermediate_representation: select Macros.Name, Macros.Cell_Library from Macros where Macros.Cell_Library = 'sky130_fd_sc_hdll' order by Macros.Size_Width desc limit 1
SQL: 
```sql
SELECT Name, Cell_Library FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hdll' ORDER BY Size_Width DESC LIMIT 1
```

Q: "Find the cells that have more than three input pins with capacitance greater than 0.005."
Schema_links: [Cells.Name,Cells.Cell_ID = Input_Pins.Cell_ID,Input_Pins.Capacitance]
A: Let's think step by step. "Find the cells that have more than three input pins with capacitance greater than 0.005." can be solved by knowing the answer to the following sub-question "What are the cells with more than three input pins having capacitance greater than 0.005?".
The SQL query for the sub-question "What are the cells with more than three input pins having capacitance greater than 0.005?" is SELECT T1.Name FROM Cells AS T1 JOIN Input_Pins AS T2 ON T1.Cell_ID = T2.Cell_ID WHERE T2.Capacitance > 0.005 GROUP BY T1.Cell_ID HAVING count(*) > 3
So, the answer to the question "Find the cells that have more than three input pins with capacitance greater than 0.005." is =
Intermediate_representation: select Cells.Name from Cells where count(Input_Pins.Input_Pin_ID) > 3 and Input_Pins.Capacitance > 0.005 group by Cells.Cell_ID
SQL: 
```sql
SELECT T1.Name FROM Cells AS T1 JOIN Input_Pins AS T2 ON T1.Cell_ID = T2.Cell_ID WHERE T2.Capacitance > 0.005 GROUP BY T1.Cell_ID HAVING count(*) > 3
```

Q: "Find the average input pin capacitance for each cell library at standard operating conditions."
Schema_links: [Input_Pins.Capacitance, Input_Pins.Cell_ID = Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Cell_Library, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. "Find the average input pin capacitance for each cell library at standard operating conditions." can be solved by grouping the input pin capacitance values by cell library and calculating their average.
The SQL query needs to join Input_Pins with Cells to get the Condition_ID, then join with Operating_Conditions to filter and group by Cell_Library.
So, the answer to the question "Find the average input pin capacitance for each cell library at standard operating conditions." is =
Intermediate_representation: select oc.Cell_Library, avg(ip.Capacitance) from Input_Pins ip join Cells c on ip.Cell_ID = c.Cell_ID join Operating_Conditions oc on c.Condition_ID = oc.Condition_ID where oc.Temperature = 25.0 and oc.Voltage = 1.8 group by oc.Cell_Library
SQL: 
```sql
SELECT oc.Cell_Library, AVG(ip.Capacitance) FROM Input_Pins ip JOIN Cells c ON ip.Cell_ID = c.Cell_ID JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 1.8 GROUP BY oc.Cell_Library
```

Q: "Find the cells with the highest maximum output pin capacitance in each cell library under standard operating conditions."
Schema_links: [Cells.Name, Cells.Cell_ID, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Cell_Library, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8, Output_Pins.Cell_ID = Cells.Cell_ID, Output_Pins.Max_Capacitance]
A: Let's think step by step. "Find the cells with the highest maximum output pin capacitance in each cell library under standard operating conditions." requires finding the maximum capacitance value for each cell library, then finding the cells that match those values.
The query will need to join Cells, Operating_Conditions, and Output_Pins tables, then use either a window function or a correlated subquery to find the cells with the maximum values per library.
So, the answer to the question "Find the cells with the highest maximum output pin capacitance in each cell library under standard operating conditions." is =
Intermediate_representation: select oc.Cell_Library, c.Name, op.Max_Capacitance from Cells c join Operating_Conditions oc on c.Condition_ID = oc.Condition_ID join Output_Pins op on c.Cell_ID = op.Cell_ID where oc.Temperature = 25.0 and oc.Voltage = 1.8 and op.Max_Capacitance = (select max(op2.Max_Capacitance) from Output_Pins op2 join Cells c2 on op2.Cell_ID = c2.Cell_ID join Operating_Conditions oc2 on c2.Condition_ID = oc2.Condition_ID where oc2.Cell_Library = oc.Cell_Library and oc2.Temperature = 25.0 and oc2.Voltage = 1.8)
SQL: 
```sql
SELECT oc.Cell_Library, c.Name, op.Max_Capacitance FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 1.8 AND op.Max_Capacitance = (SELECT MAX(op2.Max_Capacitance) FROM Output_Pins op2 JOIN Cells c2 ON op2.Cell_ID = c2.Cell_ID JOIN Operating_Conditions oc2 ON c2.Condition_ID = oc2.Condition_ID WHERE oc2.Cell_Library = oc.Cell_Library AND oc2.Temperature = 25.0 AND oc2.Voltage = 1.8)
```

Q: "Find the routing layers with resistance per square greater than 10 in the high density library."
Schema_links: [Routing_Layers.Name, Routing_Layers.Resistance_Per_SQ, 10, Routing_Layers.Cell_Library, sky130_fd_sc_hd, Routing_Layers.Corner, nom]
A: Let's think step by step. "Find the routing layers with resistance per square greater than 10 in the high density library." requires finding routing layers that meet a specific resistance threshold in a particular library.
The SQL query will need to filter the Routing_Layers table by Resistance_Per_SQ, Cell_Library, and Corner.
So, the answer to the question "Find the routing layers with resistance per square greater than 10 in the high density library." is =
Intermediate_representation: select Name, Resistance_Per_SQ from Routing_Layers where Resistance_Per_SQ > 10 and Cell_Library = 'sky130_fd_sc_hd' and Corner = 'nom' order by Resistance_Per_SQ desc
SQL: 
```sql
SELECT Name, Resistance_Per_SQ FROM Routing_Layers WHERE Resistance_Per_SQ > 10 AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Resistance_Per_SQ DESC
```

Q: "Count the number of via definitions between each pair of adjacent metal layers in the high speed library."
Schema_links: [Vias.Lower_Layer, Vias.Upper_Layer, Vias.Via_ID, Vias.Cell_Library, sky130_fd_sc_hs, Vias.Corner, nom]
A: Let's think step by step. "Count the number of via definitions between each pair of adjacent metal layers in the high speed library." requires counting vias between each pair of metal layers.
The SQL query will need to group by Lower_Layer and Upper_Layer, count Via_ID, and filter by Cell_Library and Corner.
So, the answer to the question "Count the number of via definitions between each pair of adjacent metal layers in the high speed library." is =
Intermediate_representation: select Lower_Layer, Upper_Layer, count(Via_ID) from Vias where Cell_Library = 'sky130_fd_sc_hs' and Corner = 'nom' group by Lower_Layer, Upper_Layer
SQL: 
```sql
SELECT Lower_Layer, Upper_Layer, COUNT(Via_ID) FROM Vias WHERE Cell_Library = 'sky130_fd_sc_hs' AND Corner = 'nom' GROUP BY Lower_Layer, Upper_Layer
```

Q: "Find the macros in the high density library that have pins of all three directions (INPUT, OUTPUT, and INOUT)."
Schema_links: [Macros.Name, Macros.Cell_Library, sky130_fd_sc_hd, Macros.Macro_ID = Pins.Macro_ID, Pins.Direction, INPUT, OUTPUT, INOUT]
A: Let's think step by step. "Find the macros in the high density library that have pins of all three directions (INPUT, OUTPUT, and INOUT)." can be solved by knowing the answer to the following sub-questions "Find the macros in the high density library that have INPUT pins", "Find the macros in the high density library that have OUTPUT pins", and "Find the macros in the high density library that have INOUT pins".
The SQL query for the sub-question "Find the macros in the high density library that have INPUT pins" is SELECT DISTINCT m.Macro_ID FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID WHERE p.Direction = 'INPUT' AND m.Cell_Library = 'sky130_fd_sc_hd'
The SQL query for the sub-question "Find the macros in the high density library that have OUTPUT pins" is SELECT DISTINCT m.Macro_ID FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID WHERE p.Direction = 'OUTPUT' AND m.Cell_Library = 'sky130_fd_sc_hd'
The SQL query for the sub-question "Find the macros in the high density library that have INOUT pins" is SELECT DISTINCT m.Macro_ID FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID WHERE p.Direction = 'INOUT' AND m.Cell_Library = 'sky130_fd_sc_hd'
So, the answer to the question "Find the macros in the high density library that have pins of all three directions (INPUT, OUTPUT, and INOUT)." is =
Intermediate_representation: select Macros.Name from Macros where Macros.Cell_Library = 'sky130_fd_sc_hd' and Macros.Macro_ID in (select Pins.Macro_ID from Pins join Macros on Pins.Macro_ID = Macros.Macro_ID where Pins.Direction = "INPUT" and Macros.Cell_Library = 'sky130_fd_sc_hd') and Macros.Macro_ID in (select Pins.Macro_ID from Pins join Macros on Pins.Macro_ID = Macros.Macro_ID where Pins.Direction = "OUTPUT" and Macros.Cell_Library = 'sky130_fd_sc_hd') and Macros.Macro_ID in (select Pins.Macro_ID from Pins join Macros on Pins.Macro_ID = Macros.Macro_ID where Pins.Direction = "INOUT" and Macros.Cell_Library = 'sky130_fd_sc_hd')
SQL: 
```sql
SELECT m.Name FROM Macros m WHERE m.Cell_Library = 'sky130_fd_sc_hd' AND m.Macro_ID IN (SELECT p1.Macro_ID FROM Pins p1 JOIN Macros m1 ON p1.Macro_ID = m1.Macro_ID WHERE p1.Direction = 'INPUT' AND m1.Cell_Library = 'sky130_fd_sc_hd') AND m.Macro_ID IN (SELECT p2.Macro_ID FROM Pins p2 JOIN Macros m2 ON p2.Macro_ID = m2.Macro_ID WHERE p2.Direction = 'OUTPUT' AND m2.Cell_Library = 'sky130_fd_sc_hd') AND m.Macro_ID IN (SELECT p3.Macro_ID FROM Pins p3 JOIN Macros m3 ON p3.Macro_ID = m3.Macro_ID WHERE p3.Direction = 'INOUT' AND m3.Cell_Library = 'sky130_fd_sc_hd')
```


Q: "Find the total area of all cells that are flip-flops in the high density library at normal temperature and voltage."
Schema_links: [Cells.Area, Cells.Is_Flip_Flop, TRUE, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Name, Operating_Conditions.Cell_Library, sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. "Find the total area of all cells that are flip-flops in the high density library at normal temperature and voltage." can be solved by knowing the answer to the following sub-question "What is the total area of flip-flop cells in the high density library at normal temperature and voltage?".
The SQL query for the sub-question "What is the total area of flip-flop cells in the high density library at normal temperature and voltage?" is SELECT SUM(c.Area) FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE c.Is_Flip_Flop = TRUE AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
So, the answer to the question "Find the total area of all cells that are flip-flops in the high density library at normal temperature and voltage." is =
Intermediate_representation: select sum(Cells.Area) from Cells join Operating_Conditions on Cells.Condition_ID = Operating_Conditions.Condition_ID where Cells.Is_Flip_Flop = TRUE and Operating_Conditions.Cell_Library = 'sky130_fd_sc_hd' and Operating_Conditions.Temperature = 25.0 and Operating_Conditions.Voltage = 1.8
SQL: 
```sql
SELECT SUM(c.Area) FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE c.Is_Flip_Flop = TRUE AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
```


Q: "Find the cells that have both buffer and inverter functionality in the high density library at normal temperature and voltage."
Schema_links: [Cells.Name, Cells.Is_Buffer, TRUE, Cells.Is_Inverter, TRUE, Cells.Condition_ID = Operating_Conditions.Condition_ID, Operating_Conditions.Cell_Library, sky130_fd_sc_hd, Operating_Conditions.Temperature, 25.0, Operating_Conditions.Voltage, 1.8]
A: Let's think step by step. "Find the cells that have both buffer and inverter functionality in the high density library at normal temperature and voltage." can be solved by knowing the answer to the following sub-questions "Find the cells that have buffer functionality in the high density library at normal conditions" and "Find the cells that have inverter functionality in the high density library at normal conditions".
The SQL query for the sub-question "Find the cells that have buffer functionality in the high density library at normal conditions" is SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE c.Is_Buffer = TRUE AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
The SQL query for the sub-question "Find the cells that have inverter functionality in the high density library at normal conditions" is SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE c.Is_Inverter = TRUE AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
So, the answer to the question "Find the cells that have both buffer and inverter functionality in the high density library at normal temperature and voltage." is =
Intermediate_representation: select c.Name from Cells c join Operating_Conditions oc on c.Condition_ID = oc.Condition_ID where c.Is_Buffer = TRUE and c.Is_Inverter = TRUE and oc.Cell_Library = 'sky130_fd_sc_hd' and oc.Temperature = 25.0 and oc.Voltage = 1.8
SQL: 
```sql
SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE c.Is_Buffer = TRUE AND c.Is_Inverter = TRUE AND oc.Cell_Library = 'sky130_fd_sc_hd' AND oc.Temperature = 25.0 AND oc.Voltage = 1.8
```


Q: "Find the macros whose width is greater than the average width of all macros in their respective cell library."
Schema_links: [Macros.Name,Macros.Size_Width,Macros.Cell_Library]
A: Let's think step by step. "Find the macros whose width is greater than the average width of all macros in their respective cell library." can be solved by knowing the answer to the following sub-question "What is the average width of macros grouped by cell library?".
The SQL query for the sub-question "What is the average width of macros grouped by cell library?" is SELECT Cell_Library, AVG(Size_Width) FROM Macros GROUP BY Cell_Library
So, the answer to the question "Find the macros whose width is greater than the average width of all macros in their respective cell library." is =
Intermediate_representation: select m1.Name from Macros m1 where m1.Size_Width > (select avg(m2.Size_Width) from Macros m2 where m2.Cell_Library = m1.Cell_Library)
SQL: 
```sql
SELECT m1.Name FROM Macros m1 WHERE m1.Size_Width > (SELECT AVG(m2.Size_Width) FROM Macros m2 WHERE m2.Cell_Library = m1.Cell_Library)
```

[Instructions]
- You must output your answer in the same format as the given examples.

"""


#### Cypher Query Generators ######

CYPHER_EASY_SYS_PROMPT = lambda node_descr, relationship_descr: f"""
Use the schema links to generate the correct Cypher query for the given question.

###
Here is the schema of the Physical Design graph database with node descriptions:
###

{node_descr}

Relationships:
{relationship_descr}
""" + """
Q: "Find all cells with cell_name starting with 'sky130_fd_sc_hd__buf' that are buffers."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.cell_name, 'sky130_fd_sc_hd__buf%', Cell.is_buf, true]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
WHERE c.cell_name STARTS WITH 'sky130_fd_sc_hd__buf' AND c.is_buf = true 
RETURN c.cell_name
```

Q: "How many cells are available in this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, COUNT(Cell)]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN COUNT(c)
```

Q: "What is the die area of this design?"
Schema_links: [Design, Design.die_area]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'floorplan'}}) 
RETURN d.die_area
```

Q: "How many buffer cells are present in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_buf, true]
Cypher: 
```cypher
MATCH (:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell {{is_buf: true}}) 
RETURN COUNT(c)
```

Q: "What is the name of the cell that has the largest area in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.cell_name, Cell.area, ORDER BY, LIMIT]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN c.cell_name 
ORDER BY c.area DESC 
LIMIT 1
```

Q: "Find all ports on the design's left boundary."
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.x, Design.xmin]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port) 
WHERE p.x = d.xmin 
RETURN p.port_name
```

Q: "What is the total cell area of this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, SUM(Cell.area)]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN SUM(c.area)
```

Q: "How many ports are available in this design?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, COUNT(Port)]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(p:Port) 
RETURN COUNT(p)
```

Q: "How many input ports are present in the design?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.direction, 'INPUT']
Cypher: 
```cypher
MATCH (:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(:Port {{direction: 'INPUT'}}) 
RETURN COUNT(*) as num_input_pins
```

Q: "Which net has the largest fanout?"
Schema_links: [Design, Design-[:CONTAINS_NET]->Net, Net.net_name, Net.fanout, ORDER BY, LIMIT]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) 
RETURN n.net_name 
ORDER BY n.fanout DESC 
LIMIT 1
```

Q: "What is the percentage of sequential cells in this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_seq, COUNT, percentage calculation]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
WITH COUNT(c) AS totalCells, SUM(CASE WHEN c.is_seq = true THEN 1 ELSE 0 END) AS seqCells 
RETURN (toFloat(seqCells) / totalCells) * 100 AS percentageSequentialCells
```

Q: "How many cells are electrically isolated (not connected to any nets)?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, NOT Cell-[:CONNECTS_TO]->Net]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
WHERE NOT (c)-[:CONNECTS_TO]->(:Net) 
RETURN COUNT(c)
```

Q: "Find all sequential cells in the clock network and their locations."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_seq, true, Cell.is_in_clk, true, Cell.x0, Cell.y0]
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
WHERE c.is_seq = true AND c.is_in_clk = true 
RETURN c.cell_name, c.x0, c.y0
```

[Instructions]
- You must output your answer in the same format as the given examples.
- Always filter Design nodes by stage (e.g., `{{stage: 'routing'}}`)
- If the question doesn't specify a stage, use 'routing' as the default stage
- Make sure to properly connect nodes through their relationships (e.g., always use the proper relationship between Design and other node types)
"""

CYPHER_NON_NESTED_SYS_PROMPT = lambda node_descr, relationship_descr: f"""
# Use the schema links and Intermediate_representation to generate the Cypher queries for each of the questions.

###
Here is the schema of the Physical Design graph database with node descriptions:
###

{node_descr}

Relationships:
{relationship_descr}
""" + """
Q: "How many cells are available in this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, COUNT(Cell)]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return count(c)
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN COUNT(c)
```

Q: "What is the percentage of sequential cells in this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_seq, COUNT, percentage calculation]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) with count(c) as totalCells, sum(case when c.is_seq = true then 1 else 0 end) as seqCells return (toFloat(seqCells) / totalCells) * 100 as percentageSequentialCells
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
WITH COUNT(c) AS totalCells, SUM(CASE WHEN c.is_seq = true THEN 1 ELSE 0 END) AS seqCells 
RETURN (toFloat(seqCells) / totalCells) * 100 AS percentageSequentialCells
```

Q: "How many buffer cells are present in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_buf, true]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell {{{{is_buf: true}}}}) return count(c)
Cypher: 
```cypher
MATCH (:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell {{{{is_buf: true}}}}) 
RETURN COUNT(c)
```

Q: "What is the total cell area of this design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, SUM(Cell.area)]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return sum(c.area)
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN SUM(c.area)
```

Q: "How many ports are available in this design?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, COUNT(Port)]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:HAS_PORT]->Port]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(p:Port) return count(p)
Cypher: 
```cypher
MATCH (d:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(p:Port) 
RETURN COUNT(p)
```

Q: "How many input ports are present in the design?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.direction, 'INPUT']
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:HAS_PORT]->Port]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(p:Port {{direction: 'INPUT'}}) return count(p) as num_input_pins
Cypher: 
```cypher
MATCH (:Design {{stage: 'floorplan'}})-[:HAS_PORT]->(:Port {{direction: 'INPUT'}}) 
RETURN COUNT(*) as num_input_pins
```

Q: "Which ports are placed on the bottom side of the design?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.y, Design.ymin]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:HAS_PORT]->Port]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port) where p.y = d.ymin return p
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port) 
WHERE p.y = d.ymin 
RETURN p
```

Q: "Which net has the largest fanout?"
Schema_links: [Design, Design-[:CONTAINS_NET]->Net, Net.net_name, Net.fanout, ORDER BY, LIMIT]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_NET]->Net]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) return n.net_name order by n.fanout desc limit 1
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) 
RETURN n.net_name 
ORDER BY n.fanout DESC 
LIMIT 1
```

Q: "What is the name of the cell that has the largest area in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.cell_name, Cell.area, ORDER BY, LIMIT]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return c.cell_name order by c.area desc limit 1
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN c.cell_name 
ORDER BY c.area DESC 
LIMIT 1
```

Q: "For each cell pin with negative slack, return the pin and its corresponding cell."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:HAS_PIN]->CellInternalPin, CellInternalPin.pin_slack, <0]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell-[:HAS_PIN]->CellInternalPin]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) where p.pin_slack < 0 return p.pin_name, c.cell_name
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) 
WHERE p.pin_slack < 0 
RETURN p.pin_name, c.cell_name
```

Q: "Count the number of cells for each cell_name in the design."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.cell_name, COUNT(Cell), GROUP BY Cell.cell_name]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return c.cell_name, count(c) as cell_count order by cell_count desc
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) 
RETURN c.cell_name, COUNT(c) as cell_count 
ORDER BY cell_count DESC
```

Q: "Which metal layers are used for routing the power delivery network in the design?"
Schema_links: [Design, Design-[:CONTAINS_NET]->Net, Net.signal_type, ['POWER', 'GROUND'], Net-[:ROUTED_ON]->Segment, Segment.layer]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_NET]->Net-[:ROUTED_ON]->Segment]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) where n.signal_type in ['POWER', 'GROUND'] match (n)-[:ROUTED_ON]->(s:Segment) return distinct s.layer
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_NET]->(n:Net) 
WHERE n.signal_type IN ['POWER', 'GROUND'] 
MATCH (n)-[:ROUTED_ON]->(s:Segment) 
RETURN DISTINCT s.layer
```

Q: "What is the name of the cell that drives the largest number of other cells in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:DRIVES]->Cell, COUNT]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:CONTAINS_CELL]->Cell-[:DRIVES]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:DRIVES]->(c2:Cell) with c, count(c2) as numDrivenCells order by numDrivenCells desc return c.cell_name, numDrivenCells limit 1
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:DRIVES]->(c2:Cell) 
WITH c, COUNT(c2) AS numDrivenCells 
ORDER BY numDrivenCells DESC 
RETURN c.cell_name, numDrivenCells 
LIMIT 1
```

Q: "What is the name of the cell that is connected to the rst_i port?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port.port_name, 'rst_i', Port-[:DRIVES_NET]->Net, Net-[:CONNECTS_TO]->Cell]
A: Let's think step by step. For creating the Cypher query for the given question, we need to match these patterns = [Design-[:HAS_PORT]->Port-[:DRIVES_NET]->Net-[:CONNECTS_TO]->Cell]. First, create an intermediate representation, then use it to construct the Cypher query.
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port {{port_name: 'rst_i'}})-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c:Cell) return c.cell_name
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port {{port_name: 'rst_i'}})-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c:Cell) 
RETURN c.cell_name
```

[Instructions]
- You must output your answer in the same format as the given examples.
- Always filter Design nodes by stage (e.g., `{{stage: 'routing'}}`)
- If the question doesn't specify a stage, use 'routing' as the default stage
- Make sure to properly connect nodes through their relationships (e.g., always use the proper relationship between Design and other node types)
"""


CYPHER_NESTED_COMPLEX_SYS_PROMPT = lambda node_descr, relationship_descr: f""" 
# Use the intermediate representation and the schema links to generate the Cypher queries for each of the questions.

###
Here is the schema of the Physical Design graph database with node descriptions:
###

{node_descr}

Relationships:
{relationship_descr}
""" + """
Q: "Find cells that have more pins than the average number of pins per cell."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:HAS_PIN]->CellInternalPin, COUNT(CellInternalPin), AVG(COUNT(CellInternalPin))]
A: Let's think step by step. "Find cells that have more pins than the average number of pins per cell." can be solved by knowing the answer to the following sub-question "What is the average number of pins per cell?".
The Cypher query for the sub-question "What is the average number of pins per cell?" is MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) WITH c, COUNT(p) AS pinCount RETURN AVG(pinCount) AS avgPinsPerCell
So, the answer to the question "Find cells that have more pins than the average number of pins per cell." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin) with c, count(p) as pinCount where pinCount > (match (d2:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c2:Cell)-[:HAS_PIN]->(p2:CellInternalPin) with c2, count(p2) as pc return avg(pc)) return c.cell_name, pinCount order by pinCount desc
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WITH c
MATCH (c)-[:HAS_PIN]->(p:CellInternalPin)
WITH c, COUNT(p) AS pinCount
WHERE pinCount > (
  MATCH (d2:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c2:Cell)-[:HAS_PIN]->(p2:CellInternalPin)
  WITH c2, COUNT(p2) AS pc
  RETURN AVG(pc)
)
RETURN c.cell_name, pinCount
ORDER BY pinCount DESC
```

Q: "Find cells that don't have any pins."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, NOT Cell-[:HAS_PIN]->CellInternalPin]
A: Let's think step by step. "Find cells that don't have any pins." can be solved by finding cells without any HAS_PIN relationships.
The Cypher query needs to match cells that don't have any HAS_PIN relationships to CellInternalPin nodes.
So, the answer to the question "Find cells that don't have any pins." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) where not (c)-[:HAS_PIN]->() return c.cell_name
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WHERE NOT (c)-[:HAS_PIN]->()
RETURN c.cell_name
```

Q: "Find cells that have at least one pin with negative slack and at least one pin with positive slack."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:HAS_PIN]->CellInternalPin, CellInternalPin.pin_slack, <0, >0]
A: Let's think step by step. "Find cells that have at least one pin with negative slack and at least one pin with positive slack." can be solved by finding cells that satisfy both conditions.
The Cypher query needs to match cells that have at least one pin with negative slack and also have at least one pin with positive slack.
So, the answer to the question "Find cells that have at least one pin with negative slack and at least one pin with positive slack." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) where (c)-[:HAS_PIN]->(:CellInternalPin {{direction: 'OUTPUT'}}) and (c)-[:HAS_PIN]->(:CellInternalPin) where exists {{ match (c)-[:HAS_PIN]->(p1:CellInternalPin) where p1.pin_slack < 0 }} and exists {{ match (c)-[:HAS_PIN]->(p2:CellInternalPin) where p2.pin_slack > 0 }} return c.cell_name
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WHERE 
  EXISTS {{ MATCH (c)-[:HAS_PIN]->(p1:CellInternalPin) WHERE p1.pin_slack < 0 }}
  AND
  EXISTS {{ MATCH (c)-[:HAS_PIN]->(p2:CellInternalPin) WHERE p2.pin_slack > 0 }}
RETURN c.cell_name
```

Q: "Find cells that are connected to nets that are not connected to any port."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:CONNECTS_TO]->Net, NOT Net-[:CONNECTS_TO]->Port]
A: Let's think step by step. "Find cells that are connected to nets that are not connected to any port." can be solved by finding nets that don't connect to ports, then finding cells connected to those nets.
The Cypher query needs to match nets that don't have CONNECTS_TO relationships to Port nodes, then find cells connected to those nets.
So, the answer to the question "Find cells that are connected to nets that are not connected to any port." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:CONNECTS_TO]->(n:Net) where not (n)-[:CONNECTS_TO]->(:Port) return distinct c.cell_name
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:CONNECTS_TO]->(n:Net)
WHERE NOT (n)-[:CONNECTS_TO]->(:Port)
RETURN DISTINCT c.cell_name
```

Q: "Which cell has the largest output pin transition time in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:HAS_PIN]->CellInternalPin, CellInternalPin.direction, 'OUTPUT', CellInternalPin.pin_transition, ORDER BY, LIMIT]
A: Let's think step by step. "Which cell has the largest output pin transition time in the design?" can be solved by finding the output pin with the maximum transition time and its corresponding cell.
The Cypher query needs to match cells with output pins, order them by pin_transition in descending order, and limit to the top result.
So, the answer to the question "Which cell has the largest output pin transition time in the design?" is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {{direction: 'OUTPUT'}}) return c.cell_name order by p.pin_transition desc limit 1
Cypher: 
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)-[:HAS_PIN]->(p:CellInternalPin {{direction: 'OUTPUT'}})
RETURN c.cell_name
ORDER BY p.pin_transition DESC
LIMIT 1
```

Q: "Find cells with area greater than the average area of all cells in the design."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.area, AVG(Cell.area)]
A: Let's think step by step. "Find cells with area greater than the average area of all cells in the design." can be solved by knowing the answer to the following sub-question "What is the average area of all cells in the design?".
The Cypher query for the sub-question "What is the average area of all cells in the design?" is MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) RETURN AVG(c.area) AS avgArea
So, the answer to the question "Find cells with area greater than the average area of all cells in the design." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) where c.area > (match (d2:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c2:Cell) return avg(c2.area)) return c.cell_name, c.area order by c.area desc
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WHERE c.area > (
  MATCH (d2:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c2:Cell)
  RETURN AVG(c2.area)
)
RETURN c.cell_name, c.area
ORDER BY c.area DESC
```

Q: "Find all cells that are connected to both power and ground nets."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:CONNECTS_TO]->Net, Net.signal_type, 'POWER', 'GROUND']
A: Let's think step by step. "Find all cells that are connected to both power and ground nets." can be solved by finding cells that are connected to power nets and also connected to ground nets.
The Cypher query needs to match cells that have CONNECTS_TO relationships to both types of nets.
So, the answer to the question "Find all cells that are connected to both power and ground nets." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) where (c)-[:CONNECTS_TO]->(:Net {{signal_type: 'POWER'}}) and (c)-[:CONNECTS_TO]->(:Net {{signal_type: 'GROUND'}}) return c.cell_name
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WHERE (c)-[:CONNECTS_TO]->(:Net {{signal_type: 'POWER'}})
  AND (c)-[:CONNECTS_TO]->(:Net {{signal_type: 'GROUND'}})
RETURN c.cell_name
```

Q: "What is the distribution of cells by type (buffer, inverter, sequential, etc.) in the design?"
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell.is_buf, Cell.is_inv, Cell.is_seq, COUNT, percentage]
A: Let's think step by step. "What is the distribution of cells by type in the design?" can be solved by counting cells of each type and calculating percentages.
The Cypher query needs to count cells with different properties and determine the percentage of each type.
So, the answer to the question "What is the distribution of cells by type in the design?" is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) with count(c) as totalCells match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return "Buffer" as type, count(c {{is_buf: true}}) as count, (count(c {{is_buf: true}}) * 100.0 / totalCells) as percentage union match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) with count(c) as totalCells match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return "Inverter" as type, count(c {{is_inv: true}}) as count, (count(c {{is_inv: true}}) * 100.0 / totalCells) as percentage union match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) with count(c) as totalCells match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) return "Sequential" as type, count(c {{is_seq: true}}) as count, (count(c {{is_seq: true}}) * 100.0 / totalCells) as percentage
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WITH COUNT(c) AS totalCells
RETURN 
  "Buffer" AS type, 
  SUM(CASE WHEN c.is_buf = true THEN 1 ELSE 0 END) AS count,
  (SUM(CASE WHEN c.is_buf = true THEN 1 ELSE 0 END) * 100.0 / totalCells) AS percentage
UNION
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WITH COUNT(c) AS totalCells
RETURN 
  "Inverter" AS type, 
  SUM(CASE WHEN c.is_inv = true THEN 1 ELSE 0 END) AS count,
  (SUM(CASE WHEN c.is_inv = true THEN 1 ELSE 0 END) * 100.0 / totalCells) AS percentage
UNION
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WITH COUNT(c) AS totalCells
RETURN 
  "Sequential" AS type, 
  SUM(CASE WHEN c.is_seq = true THEN 1 ELSE 0 END) AS count,
  (SUM(CASE WHEN c.is_seq = true THEN 1 ELSE 0 END) * 100.0 / totalCells) AS percentage
```

Q: "Find cells that only connect to high-fanout nets (fanout > 10)."
Schema_links: [Design, Design-[:CONTAINS_CELL]->Cell, Cell-[:CONNECTS_TO]->Net, Net.fanout, >10, NOT]
A: Let's think step by step. "Find cells that only connect to high-fanout nets (fanout > 10)." can be solved by finding cells that don't connect to any nets with fanout <= 10.
The Cypher query needs to match cells that connect to nets, ensure all connected nets have fanout > 10.
So, the answer to the question "Find cells that only connect to high-fanout nets (fanout > 10)." is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell) where not (c)-[:CONNECTS_TO]->(:Net {{fanout: 10}}) and (c)-[:CONNECTS_TO]->(:Net) return c.cell_name
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:CONTAINS_CELL]->(c:Cell)
WHERE (c)-[:CONNECTS_TO]->(:Net)
  AND NOT (c)-[:CONNECTS_TO]->(:Net WHERE n.fanout <= 10)
RETURN c.cell_name
```

Q: "Which ports have connections to sequential cells through exactly one combinational cell?"
Schema_links: [Design, Design-[:HAS_PORT]->Port, Port-[:DRIVES_NET]->Net, Net-[:CONNECTS_TO]->Cell, Cell.is_seq, false, Cell-[:DRIVES]->Cell, Cell.is_seq, true]
A: Let's think step by step. "Which ports have connections to sequential cells through exactly one combinational cell?" can be solved by tracing paths from ports through nets and cells.
The Cypher query needs to find paths from ports to sequential cells with exactly one combinational cell in between.
So, the answer to the question "Which ports have connections to sequential cells through exactly one combinational cell?" is =
Intermediate_representation: match (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port)-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c1:Cell)-[:DRIVES]->(c2:Cell) where c1.is_seq = false and c2.is_seq = true return distinct p.port_name
Cypher:
```cypher
MATCH (d:Design {{stage: 'routing'}})-[:HAS_PORT]->(p:Port)-[:DRIVES_NET]->(n:Net)-[:CONNECTS_TO]->(c1:Cell)-[:DRIVES]->(c2:Cell)
WHERE c1.is_seq = false AND c2.is_seq = true
RETURN DISTINCT p.port_name
```

[Instructions]
- You must output your answer in the same format as the given examples.
- Always filter Design nodes by stage (e.g., `{{stage: 'routing'}}`)
- If the question doesn't specify a stage, use 'routing' as the default stage
- Make sure to properly connect nodes through their relationships (e.g., always use the proper relationship between Design and other node types)
"""