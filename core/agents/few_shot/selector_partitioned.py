from core.agents.few_shot.demo import Demo
from core.database.sql import get_desc, get_fk

# Selector lib few shot
selector_lib_few_shot_partition = [
    Demo(
        input="What is the number of cells in high density library ?",
        source="Liberty",
        scl_variant="HighDensity",
        query= "SELECT COUNT(*) FROM Cells",
        desc_str = get_desc("Liberty", partition=True),
        fk_str = get_fk("Liberty", partition=True),
        selection_steps = """
1) "Cells" is kept because:
It contains the primary information about all gates.

2) "Input_Pins" and "Output_Pins" are dropped because:
The query only asks for a list of gates, not their pin details.

3) "Timing_Values" is dropped because:
No timing information is required for simply listing gates.
""",
        tables = """
```json
"Cells": "keep",
"Input_Pins": "drop",
"Output_Pins": "drop",
"Timing_Values": "drop",
```
"""
    ).to_dict(),  
    
    Demo(
        input="List the input and output pin names for the sky130_fd_sc_ms__nand2_1",
        source="Liberty",
        scl_variant="MediumSpeed",
        query= "",
        desc_str = get_desc("Liberty", partition=True),
        fk_str = get_fk("Liberty", partition=True),
        selection_steps = """
1) "Cells" is kept because:
We need to identify the specific cell (sky130_fd_sc_ms__nand2_1).

2) "Input_Pins" is kept because:
We need to list the input pin names for the specified cell.

3) "Output_Pins" is kept because:
We need to list the output pin names for the specified cell.

4) "Timing_Values" is dropped because:
The query doesn't ask for any timing information.
""",
        tables = """
```json
"Cells": "keep",
"Input_Pins": "keep",
"Output_Pins": "keep",
"Timing_Values": "drop"
```
        """
    ).to_dict(),    
    
    Demo(
        input="Print the rise propagation delay along with the values of table indicies in a table format for the sky130_fd_sc_hd__xnor3_2 cell for all of its input pins ?",
        source="Liberty",
        scl_variant="HD",
        query= "",
        desc_str = get_desc("Liberty", partition=True),
        fk_str = get_fk("Liberty", partition=True),
        selection_steps ="""
1) "Cells" is kept because:
We need to identify the specific cell (sky130_fd_sc_hd__xnor3_2).

2) "Input_Pins" is kept because:
We need to identify all input pins of the specified cell. Timing path starts at an input pin so we need to keep the input pins table.

3) "Output_Pins" is kept because:
Output pin information are needed to complete the timing path information. Timing path ends at the output pin so we need to keep the output pins table.
Output pin ID is needed to query the right entry in the timing tables, so it must be marked as kept. 

4) "Timing_Values" is kept because:
It likely contains the structure of timing information, including rise propagation delay.

For timing questions, we must mark the Input_Pins and Output_Pins tables as keep because timing path is defined from an input pin to an output pin even if the question doesn't explicitly specify input and output pin details. 
""",
        tables = """
```json
"Cells": "keep",
"Input_Pins": "keep",
"Output_Pins": "keep",
"Timing_Values": "keep"
```
        """
    ).to_dict()
]


selector_lef_few_shot_partitioned = [
    Demo(
        input="What is the cell width and height for the low leakage variant",
        source="Lef",
        scl_variant="HighDenistyLowLeakage",
        query= "",
        desc_str = get_desc("Lef"),
        fk_str = get_fk("Lef"),
        selection_steps = """
1) "Macros" is kept because:
   It contains the primary information about cell dimensions, including width and height.
   This table is essential for answering questions about cell size.

2) "Pins", "Pin_Ports", "Pin_Port_Rectangles" are dropped because:
   The query doesn't ask for any information related to pins or their geometries.

3) "Obstructions" and "Obstruction_Rectangles" are dropped because:
   Obstruction information is not relevant to cell width and height.
""",
        tables = """
```json
"Macros": "keep",
"Pins": "drop",
"Pin_Ports": "drop",
"Pin_Port_Rectangles": "drop",
"Obstructions": "drop",
"Obstruction_Rectangles": "drop",  
```
        """
    ).to_dict(),    
    
    Demo(
        input="Which pin has the smallest area for the sky130_fd_sc_hd__xnor3_2 gate",
        source="Lef",
        scl_variant="HighDensity",
        query= "",
        desc_str = get_desc("Lef"),
        fk_str = get_fk("Lef"),
        selection_steps = """
1) "Macros" is kept because:
   We need to identify the specific gate (sky130_fd_sc_hd__xnor3_2).

2) "Pins" is kept because:
   It contains the primary information about pins, which is necessary to compare their areas.

3) "Pin_Ports" and "Pin_Port_Rectangles" are kept because:
   These tables likely contain the geometric information needed to calculate pin areas.

4) "Obstructions" and "Obstruction_Rectangles" are dropped because:
   Obstruction information is not relevant to pin areas.
""",
        tables = """
```json
"Macros": "keep",
"Pins": "keep",
"Pin_Ports": "keep",
"Pin_Port_Rectangles": "keep",
"Obstructions": "drop",
"Obstruction_Rectangles": "drop",  
```
        """
    ).to_dict(),  
    
    Demo(
        input="List the number of obstruction rectangles present in the sky130_fd_sc_hd__xnor3_2 cell layout",
        source="Lef",
        scl_variant="HighDensity",
        query= "",
        desc_str = get_desc("Lef"),
        fk_str = get_fk("Lef"),
        selection_steps = """
1) "Macros" is kept because:
   We need to identify the Macro_ID for the specific gate (sky130_fd_sc_hd__xnor3_2).

2) "Obstructions" is kept because:
   It contains the primary information about obstruction layers in the gate layout.

3) "Pins", "Pin_Ports", and "Pin_Port_Rectangles" are dropped because:
   The query doesn't ask for any information related to pins or their geometries.

4) "Obstruction_Rectangles" is kept because:
  It contains the obstruction rectangle information.
""",
        tables = """
```json
"Macros": "keep",
"Pins": "drop",
"Pin_Ports": "drop",
"Pin_Port_Rectangles": "drop",
"Obstructions": "keep",
"Obstruction_Rectangles": "keep",  
```
        """
    ).to_dict()
]

selector_tlef_few_shot_partitioned = [
    
    Demo(
        input="List the routing layers available in the PDK and their corresponding width",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query= "",
        desc_str = get_desc("TechnologyLef", partition=True),
        fk_str = get_fk("TechnologyLef", partition=True),
        selection_steps = """
1) "Routing_Layers" is kept because:
   It contains the primary information about routing layers and their properties, including width.

2) "Antenna_Diff_Side_Area_Ratios", "Antenna_Diff_Area_Ratios" are dropped because:
   These antenna-related tables are not relevant to listing routing layers and their widths.

3) "Cut_Layers" is dropped because:
   Cut layers are not required for this query.

4) "Vias" and "Via_Layers" are dropped because:
   Via information is not relevant to listing routing layers and their widths.
""",
        tables = """
```json
"Routing_Layers": "keep",
"Antenna_Diff_Side_Area_Ratios": "drop",
"Cut_Layers": "drop",
"Antenna_Diff_Area_Ratios": "drop",
"Vias": "drop",
"Via_Layers": "drop"
```
"""
    ).to_dict(), 
    
    Demo(
        input="List the via names available in the PDK",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query= "",
        desc_str = get_desc("TechnologyLef", partition=True),
        fk_str = get_fk("TechnologyLef", partition=True),
        selection_steps = """
1) "Vias" is kept because:
   It contains the primary information about vias, including their names.

2) "Routing_Layers", "Cut_Layers", and "Via_Layers" are dropped because:
    The query only asks for via names, which should be in the "Vias" table.

3) "Antenna_Diff_Side_Area_Ratios" and "Antenna_Diff_Area_Ratios" are dropped because:
   These antenna-related tables are not relevant to listing via names.
""",
        tables = """
```json
"Routing_Layers": "drop",
"Antenna_Diff_Side_Area_Ratios": "drop",
"Cut_Layers": "drop",
"Antenna_Diff_Area_Ratios": "drop",
"Vias": "keep",
"Via_Layers": "drop"
```
        """
    ).to_dict(), 
    
    Demo(
        input="List metal layers ordered by thickness.",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query= "",
        desc_str = get_desc("TechnologyLef", partition=True),
        fk_str = get_fk("TechnologyLef", partition=True),
        selection_steps = """
1) "Routing_Layers" is kept because:
   It contains information about metal layers, including their thickness.

2) "Antenna_Diff_Side_Area_Ratios" and "Antenna_Diff_Area_Ratios" are dropped because:
   These antenna-related tables are not relevant to metal layer thickness.

3) "Cut_Layers" is dropped because:
   Cut layers are different from metal layers and not required for this query.

4) "Vias" and "Via_Layers" are dropped because:
   Via information is not relevant to listing metal layers by thickness.
""",
        tables = """
```json
"Routing_Layers": "keep",
"Antenna_Diff_Side_Area_Ratios": "drop",
"Cut_Layers": "drop",
"Antenna_Diff_Area_Ratios": "drop",
"Vias": "drop",
"Via_Layers": "drop",  
```
"""
    ).to_dict(),
    
]

selector_few_shot_partition = selector_lib_few_shot_partition + selector_lef_few_shot_partitioned + selector_tlef_few_shot_partitioned
