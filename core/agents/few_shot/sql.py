from core.agents.few_shot.demo import Demo
from core.database.sql import get_desc, get_fk


## Decomposer few shot examples
decomposer_tlef_fewshot = [
    Demo(
        input="List the routing layers available in the PDK",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query= "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom';",
        desc_str = get_desc("TechnologyLef"),
        fk_str = get_fk("TechnologyLef"),
        tables = """""",
        subquestions=[
            "Filter the entries in the Routing_Layers table related to the standard cell library 'sky130_fd_sc_hd' and the corner 'nom'",
            "Select the Name column from the filtered entries to list the routing layers available in the PDK"
        ],
        subqueries = [
            "SELECT * FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom';",
            "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom';"
        ]
    ).to_dict(), 
    
    Demo(
        input="What is the resistance of via2 cut in the max corner?",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query= "SELECT Resistance FROM Cut_Layers WHERE Layer_ID = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'max');",
        desc_str = get_desc("TechnologyLef"),
        fk_str = get_fk("TechnologyLef"),
        tables = """""",
        subquestions=[
           "Filter the entries in the Cut_Layers table related to the standard cell library 'sky130_fd_sc_hd' and the corner 'max'",
           "Select the resistance column from the filtered columns with Name column equal to via2",
        ],
        subqueries = [
           "SELECT * FROM Cut_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'max';",
           "SELECT Resistance FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'max';"
        ]
    ).to_dict(), 

]

decompser_lef_few_shot = [
      
    Demo(
        input="What is the cell height of the mux4_1 in the low power variant ?",
        source="Lef",
        scl_variant="LowPower",
        query= "SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_lp__mux4_1' AND Cell_Library = 'sky130_fd_sc_lp'",
        desc_str = get_desc("Lef", ["Macros"]),
        fk_str = get_fk("Lef", ["Macros"]),
        tables = """""",
        subquestions=[
            "Filter the entries in the Macros table related to the standard cell library 'sky130_fd_sc_lp'",
            "Select the Size_Height column where the macro Name is equal to 'sky130_fd_sc_lp__mux4_1'. Prefix the cell name with library name, i.e `mux4_1` in the low power library is `sky130_fd_sc_lp__mux4_1`",
        ],
        subqueries = [
           "SELECT * FROM Macros WHERE Cell_Library = 'sky130_fd_sc_lp'",
           "SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_lp__mux4_1' AND Cell_Library = 'sky130_fd_sc_lp'",
        ]
    ).to_dict(), 
   
]

decompser_lib_few_shot = [
    Demo(
        input="Count the number of cells available in the high density library.",
        source="Liberty",
        scl_variant="HighDensity",
        query= "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')",
        desc_str = get_desc("Liberty", ['Operating_Conditions', 'Cells']),
        fk_str = get_fk("Liberty", ['Operating_Conditions', 'Cells']),
        tables = """""",
        subquestions=[
           'Identify the Condition_ID for the high density library variant under the given operating conditions (temperature 25 and voltage 1.8).',
           'Filter the entries in the Cells table related to the identified Condition_ID for the high density library variant.',
           'Count the number of cells available in the filtered entries.'
        ],
        subqueries = [
           "SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd'",
           "SELECT * FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')",
           "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')",
        ]
    ).to_dict(), 
    
    Demo(
        input="What is the output pin capacitance for the sky130_fd_sc_ms__mux4_1 cell ? ",
        source="Liberty",
        scl_variant="MediumSpeed",
        query= "SELECT Max_Capacitance  FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID  FROM Cells WHERE Name = 'sky130_fd_sc_ms__mux4_1'  AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms'));",
        desc_str = get_desc("Liberty", ['Operating_Conditions', 'Cells', 'Output_Pins']),
        fk_str = get_fk("Liberty",  ['Operating_Conditions', 'Cells', 'Output_Pins']),
        tables = """""",
        subquestions=[
           'Find the Condition_ID for the operating condition with temperature 25 and voltage 1.8 for the standard cell variant sky130_fd_sc_ms.',
           'Filter entries in the Cells table related to the Condition_ID obtained in step 1 and the standard cell variant sky130_fd_sc_ms.',
           'Filter entries in the Output_Pins table related to the Cell_ID obtained in step 2',
           'Select the Max_Capacitance for the output pin of the cell with the name sky130_fd_sc_ms__mux4_1.'
        ],
        subqueries = [
           "SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms'",
           "SELECT * FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions    WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms');",
           "SELECT * FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions   WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms'));",
           "SELECT Max_Capacitance  FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID  FROM Cells WHERE Name = 'sky130_fd_sc_ms__mux4_1'  AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions   WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms'));"
        ]
    ).to_dict()
]


decomposer_few_shot = decomposer_tlef_fewshot + decompser_lef_few_shot  + decompser_lib_few_shot
