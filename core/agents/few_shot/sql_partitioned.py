from core.agents.few_shot.demo import Demo
from core.database.sql import get_desc, get_fk


## Decomposer few shot examples
decomposer_tlef_fewshot_partition = [
    Demo(
        input="List the routing layers available in the PDK",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query="SELECT Name FROM Routing_Layers",
        desc_str=get_desc("TechnologyLef", partition=True),
        fk_str=get_fk("TechnologyLef", partition=True),
        tables="",
        subquestions=[
            "Retrieve all available routing layers in the PDK.",
            "Select the Name column from the filtered entries to list the routing layers available in the PDK."
        ],
        subqueries=[
            "SELECT * FROM Routing_Layers;",
            "SELECT Name FROM Routing_Layers;"
        ]
    ).to_dict(),
    
    Demo(
        input="What is the resistance of via2 cut in the max corner?",
        source="TechnologyLef",
        scl_variant="HighDensity",
        query="SELECT Resistance FROM Cut_Layers WHERE Name = 'via2';",
        desc_str=get_desc("TechnologyLef", partition=True),
        fk_str=get_fk("TechnologyLef", partition=True),
        tables="",
        subquestions=[
            "Retrieve all columns from the Cut_Layers table to understand its structure.",
            "Select the Resistance column from the entries where the Name column is 'via2' to find the resistance of via2 cut."
        ],
        subqueries=[
            "SELECT * FROM Cut_Layers;",
            "SELECT Resistance FROM Cut_Layers WHERE Name = 'via2';"
        ]
    ).to_dict()


]

decompser_lef_few_shot_partition = [
      
    Demo(
        input="What is the cell height of the mux4_1 in the low power variant?",
        source="Lef",
        scl_variant="LowPower",
        query="SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_lp__mux4_1'",
        desc_str=get_desc("Lef", ["Macros"], partition=True),
        fk_str=get_fk("Lef", ["Macros"], partition=True),
        tables="",
        subquestions=[
            "Retrieve all columns from the Macros table to understand its structure and available attributes.",
            "Select the Size_Height column where the macro Name is equal to 'sky130_fd_sc_lp__mux4_1'. Ensure that the cell name is prefixed with the library name, i.e., 'mux4_1' in the low power library is 'sky130_fd_sc_lp__mux4_1'."
        ],
        subqueries=[
            "SELECT * FROM Macros;",
            "SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_lp__mux4_1';"
        ]
    ).to_dict()
   
]

decompser_lib_few_shot_partition = [
        Demo(
            input="Count the number of cells available in the high-density library.",
            source="Liberty",
            scl_variant="HighDensity",
            query="SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells",
            desc_str=get_desc("Liberty", ['Cells'], partition=True),
            fk_str=get_fk("Liberty", ['Cells'], partition=True),
            tables="",
            subquestions=[
                "Retrieve all available cells in the Cells table.",
                "Count the number of cells available in the high-density library."
            ],
            subqueries=[
                "SELECT * FROM Cells;",
                "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells;"
            ]
        ).to_dict(),

    
      Demo(
        input="What is the output pin capacitance for the sky130_fd_sc_ms__mux4_1 cell?",
        source="Liberty",
        scl_variant="MediumSpeed",
        query="SELECT Output_Pins.Max_Capacitance FROM Output_Pins INNER JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'sky130_fd_sc_ms__mux4_1';",
        desc_str=get_desc("Liberty", ['Cells', 'Output_Pins'], partition=True),
        fk_str=get_fk("Liberty", ['Cells', 'Output_Pins'], partition=True),
        tables="",
        subquestions=[
            "Select the Cell_ID in the Cells table where the cell Name is 'sky130_fd_sc_ms__mux4_1'.",
            "Filter entries in the Output_Pins table related to the Cell_ID obtained in step 2.",
            "Select the Max_Capacitance for the output pin of the cell 'sky130_fd_sc_ms__mux4_1'."
        ],
        subqueries=[
            "SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_ms__mux4_1';",
            "SELECT * FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_ms__mux4_1');",
            "SELECT Output_Pins.Max_Capacitance FROM Output_Pins INNER JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'sky130_fd_sc_ms__mux4_1';"
        ]
    ).to_dict()

]


decomposer_few_shot_partition = decomposer_tlef_fewshot_partition + decompser_lef_few_shot_partition  + decompser_lib_few_shot_partition
