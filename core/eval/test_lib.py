
test_queries_lib = [
    # cells table questions
    {
        # 376
        "input": "How many cells are in the high speed library?",
        "view": "Liberty",
        "scl_variant": ["HighSpeed"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs');"
        ],
    },
    {
        # 5.0048
        "input": "What is the area of the sky130_fd_sc_hdll__nand2_1 cell ? ",
        "view": "Liberty",
        "scl_variant": ["HighDensityLowLeakage"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__nand2_1'",
            "SELECT Area, Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__nand2_1'",
            "SELECT Name, Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__nand2_1'",
        ]
    },
    {
        #  0.0028884150
        "input": "What is the leakage power of the sky130_fd_sc_hdll__buf_6 cell ?",
        "view": "Liberty",
        "scl_variant": ["HighDensityLowLeakage"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
            "SELECT Leakage_Power FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__buf_6'",
            "SELECT Name, Leakage_Power FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__buf_6'",
            "SELECT Leakage_Power, Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') AND Name = 'sky130_fd_sc_hdll__buf_6';",
            ]
    },
    {
        # sky130_fd_sc_hd__diode_2
        "input": "Which cell has the smallest area in the high density library ? Give me the cell name ",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd') ORDER BY Area ASC LIMIT 1",
                "SELECT Cell_ID, Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd') ORDER BY Area ASC LIMIT 1",
                "SELECT Cell_ID, Name, Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd') ORDER BY Area ASC LIMIT 1",
            ]
    },
    {
        # sky130_fd_sc_hdll__clkbuf_12
        "input": "Which cell has the second smallest area in the high density low leakage library ? Give me the cell name",
        "view": "Liberty",
        "scl_variant": ["HighDensityLowLeakage"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
                "SELECT Cell_ID, Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
                "SELECT Cell_ID, Name, Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
                "SELECT Name, Area FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hdll' AND Temperature = 25.0 AND Voltage = 1.8) ORDER BY Area ASC LIMIT 1 OFFSET 1;",
            ]
    },
    {
        # sky130_fd_sc_hdll__diode_2
        "input": "Give the cell name with the smallest leakage power in the high density low leakage library?",
        "view": "Liberty",
        "scl_variant": ["HighDensityLowLeakage"],
        "selected_tables": ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Name FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') ORDER BY Leakage_Power ASC LIMIT 1;",
                "SELECT Name, Leakage_Power FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll') ORDER BY Leakage_Power ASC LIMIT 1; "
            ]
    },
    {
        # sky130_fd_sc_hd 428, sky130_fd_sc_hdll 324, sky130_fd_sc_hs 376
        # sky130_fd_sc_ls 386, sky130_fd_sc_ms 376
        "input": "Count the number of cells for each standard cell lirbary in the PDK.",
        "view": "Liberty",
        "scl_variant": ['HighDensity', 'HighDensityLowLeakage', 'HighSpeed', 'LowSpeed', 'MediumSpeed', 'LowPower'],
        'selected_tables': ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT o.Cell_Library, COUNT(c.Cell_ID) AS Number_of_Cells FROM Cells AS c JOIN Operating_Conditions AS o ON c.Condition_ID = o.Condition_ID WHERE o.Temperature = 25.0 AND o.Voltage = 1.8 GROUP BY o.Cell_Library;"
        ]
    },
    {
        # sky130_fd_sc_hd: 119.0081
        # sky130_fd_sc_hdll: 25.9616
        # sky130_fd_sc_hs: 0.2013
        # sky130_fd_sc_ls: 0.0440
        # sky130_fd_sc_ms: 0.0
        "input": "How does the average leakage power vary across different cell libraries?",
        "view": "Liberty",
        "scl_variant": ['HighDensity', 'HighDensityLowLeakage', 'HighSpeed', 'LowSpeed', 'MediumSpeed', 'LowPower'],
        'selected_tables': ['Operating_Conditions', 'Cells'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT oc.Cell_Library, AVG(c.Leakage_Power) AS Average_Leakage_Power FROM Cells AS c JOIN Operating_Conditions AS oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Temperature = 25.0 AND oc.Voltage = 1.8 AND oc.Cell_Library IN ('sky130_fd_sc_hd', 'sky130_fd_sc_hdll', 'sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms', 'sky130_fd_sc_lp') GROUP BY oc.Cell_Library;"
        ]
    },
    ######## Pin tables question
    ####### Input_Pins
    {
        # 5 input pins
        "input": "Count the number of input pins for the sky130_fd_sc_hd__or3_4 cell.",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT COUNT(Input_Pin_ID) AS Number_of_Input_Pins FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__or3_4')"
            ]
    },   
    {
        # A1, A2, B1, B2
        "input": "List the input pin names of the sky130_fd_sc_ms__o22ai_4 cell.",
        "view": "Liberty",
        "scl_variant": ["MediumSpeed"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
        [
        "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms') AND Name = 'sky130_fd_sc_ms__o22ai_4')",
        ]
    },
    {
        # 68 cells
        "input": "How many cells have an input clock pin in the high speed library ? ",
        "view": "Liberty",
        "scl_variant": ["HighSpeed"],
        "selected_tables": ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Input_Pins WHERE Clock = True AND Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs'));",
            ]
    },
    {
        # A1: (rise:0.0024340 , fall: 0.00226), A2: (rise:0.002527, fall: 0.0022570)
        # B1: (rise:0.002506 , fall:  0.002243), B2: (rise: 0.002487 , fall:  0.002161)
        "input": "List the input pin names for the sky130_fd_sc_hd__a22o_1 cell and their corresponding rise and fall capacitence values. ",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Input_Pin_Name, Rise_Capacitance, Fall_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd'));",
                "SELECT Input_Pin_Name, Fall_Capacitance, Rise_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd'));",
            ]
    },
    {
        # B 
        "input": "For the sky130_fd_sc_hd__or2_0 cell, which input pin has the smallest fall capacitance ?",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Input_Pin_Name FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__or2_0' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')) ORDER BY Fall_Capacitance ASC LIMIT 1",
            "SELECT Input_Pin_Name, Fall_Capacitance FROM Input_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__or2_0' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')) ORDER BY Fall_Capacitance ASC LIMIT 1"
        ]
    },
    {
        # sky130_fd_sc_hd__lpflow_clkinvkapwr_16
        "input": "Which cell has the largest input pin capacitance in the high density library? ",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Cells', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Cells.Name AS Cell_Name, Input_Pins.Capacitance AS Input_Pin_Capacitance FROM Cells JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID WHERE Cells.Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd') ORDER BY Input_Pin_Capacitance DESC LIMIT 1",
            "SELECT Cells.Name AS Cell_Name, Input_Pins.Input_Pin_Name, MAX(Input_Pins.Capacitance) AS Max_Capacitance FROM Input_Pins JOIN Cells ON Input_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) GROUP BY Cells.Cell_ID ORDER BY Max_Capacitance DESC LIMIT 1;",
            "SELECT c.Name, ip.Capacitance FROM Cells c JOIN Input_Pins ip ON c.Cell_ID = ip.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library ='sky130_fd_sc_hd') ORDER BY ip.Capacitance DESC LIMIT 1; ",
            "SELECT c.Name AS Cell_Name FROM Cells c JOIN Input_Pins ip ON c.Cell_ID = ip.Cell_ID WHERE c.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ORDER BY ip.Capacitance DESC LIMIT 1;",
            "SELECT Cells.Name  FROM Cells JOIN Operating_Conditions  ON Cells.Condition_ID = Operating_Conditions.Condition_ID JOIN Input_Pins ON Cells.Cell_ID = Input_Pins.Cell_ID WHERE Operating_Conditions.Cell_Library ='sky130_fd_sc_hd'  AND Operating_Conditions.Temperature = 25.0  AND Operating_Conditions.Voltage = 1.8 ORDER BY Input_Pins.Capacitance DESC LIMIT 1"
        ]
    },
    {
        ## clock: 0.0038468993558776142, Non-Clock Pin: 0.002046260869565216
        "input": "How does the average capacitance of clock pins compare to non-clock pins in the high density library?",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Clock, AVG(Capacitance) AS Average_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')) GROUP BY Clock"
        ]
    },
    {
        # fall: 0.00195, rise: 0.00214
        "input": "How does the average fall capacitance of clock input pins compare to their average rise capacitance in the high density library?",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Operating_Conditions', 'Input_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT AVG(Fall_Capacitance) AS Average_Fall_Capacitance, AVG(Rise_Capacitance) AS Average_Rise_Capacitance FROM Input_Pins WHERE Cell_ID IN (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')) AND Clock = 1"
        ]
    },
    #### Output_Pins
    {
        #  1.4965390000
        "input": "What is the max transition time of the sky130_fd_sc_hdll__a32oi_4 cell output pin ?",
        "view": "Liberty",
        "scl_variant": ["HighDensityLowLeakage"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
            "SELECT Max_Transition AS Max_Transition FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__a32oi_4' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll'))",
            ]
    },
    {
        # (B1&B2) | (A1&A2)
        "input": "What is the boolean function of the sky130_fd_sc_ls__a22o_1 cell output pin? ",
        "view": "Liberty",
        "scl_variant": ["LowSpeed"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Function FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_ls__a22o_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ls'))",
            ]
    },
    {
        # 0.1793100
        "input": "What is the max capacitance of the sky130_fd_sc_hs__a41oi_4 cell output pin ?  ",
        "view": "Liberty",
        "scl_variant": ["HighSpeed"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Max_Capacitance FROM Output_Pins JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name = 'sky130_fd_sc_hs__a41oi_4' AND Cells.Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs' );"
            ]
    },
    {
        # sky130_fd_sc_hd__buf_12
        "input": "Which cell has the maximum max capacitence value for its output pin in the high density library? Give me the cell name",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hd' AND Temperature = 25.0 AND Voltage = 1.8) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
                "SELECT Cell_ID, Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hd' AND Temperature = 25.0 AND Voltage = 1.8) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
                "SELECT Max_Capacitance, Name FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hd' AND Temperature = 25.0 AND Voltage = 1.8) ) ORDER BY Max_Capacitance DESC LIMIT 1;",
                "SELECT Name, Max_Capacitance FROM ( SELECT c.Cell_ID, c.Name, op.Max_Capacitance FROM Cells c JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE c.Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Cell_Library = 'sky130_fd_sc_hd' AND Temperature = 25.0 AND Voltage = 1.8) ) ORDER BY Max_Capacitance DESC LIMIT 1;"
            ]
    },
    {
        # sky130_fd_sc_hd__conb_1
        "input": "Which cell has lowest max transition time for its output pin in the high density library? Give me the cell name",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": 
            [
                "SELECT c.Name FROM Cells c JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID JOIN Output_Pins op ON c.Cell_ID = op.Cell_ID WHERE oc.Cell_Library ='sky130_fd_sc_hd' AND oc.Temperature = 25 AND oc.Voltage = 1.8 ORDER BY op.Max_Transition ASC LIMIT 1;",
                "SELECT c.Name, o.Max_Transition FROM Cells c JOIN Output_Pins o ON c.Cell_ID = o.Cell_ID JOIN Operating_Conditions oc ON c.Condition_ID = oc.Condition_ID WHERE oc.Cell_Library ='sky130_fd_sc_hd' AND oc.Temperature = 25 AND oc.Voltage = 1.8 ORDER BY o.Max_Transition ASC NULLS LAST LIMIT 1;"
            ]
    },
    {
        # 38
        "input": "How many cells have more than one output pin in the PDK? ",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT COUNT(Cell_ID) AS Number_of_Cells FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd') AND Cell_ID IN (SELECT Cell_ID FROM Output_Pins GROUP BY Cell_ID HAVING COUNT(Output_Pin_ID) > 1)",
        ]
    },
    ## Timing table questions
    {
        # proppogation delay for a specific pin and specific load and transition time values. 
        # 0.4305261000
        "input": "What is the fall propagation delay of the mux4_1 cell from related input pin A0 to the output pin with an output load of 0.0005 and input rise time of 0.01 in the high density library in the PDK ?",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins', 'Output_Pins', 'Timing_Values'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__mux4_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__mux4_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) ) AND Related_Input_Pin = 'A0' AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01"        
        ]
    },
    {
        #variable_1 : "input_net_transition";
        #variable_2 : "total_output_net_capacitance";
        ## fall and rise propogation comparios for a specific pin 
        ## cell fall: 1.6796489, cell rise: 1.5191374
        "input": "Compare both the rise and fall propogation delays of the mux4_1 cell from related input pin S0 to output pin with input transition time of 1.5 and output load of 0.161143 in the high density library in the PDK.",
        "view": "Liberty", 
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins', 'Output_Pins', 'Timing_Values'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Rise_Delay, Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__mux4_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) AND Output_Pin_ID = ( SELECT Output_Pin_ID FROM Output_Pins WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__mux4_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) ) AND Related_Input_Pin = 'S0' AND Input_Transition = 1.5 AND Output_Capacitance = 0.161143;"        
        ]
    },
    {
        # cross pin comparison propogation delay comparison 
        # A: 0.0206305000, B: 0.0240063 --> A
        "input": "Which related input pin of the nand2_1 has the lowest fall propgation delay for an output load of 0.0005 and input rise time of 0.01 in the high density library in the PDK? ",
        "view": "Liberty",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins', 'Output_Pins', 'Timing_Values'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT Related_Input_Pin FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) AND Input_Transition = 0.01 AND Output_Capacitance = 0.0005 ORDER BY Fall_Delay ASC LIMIT 1;",
            "SELECT Fall_Delay, Related_Input_Pin FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) AND Input_Transition = 0.01 AND Output_Capacitance = 0.0005 ORDER BY Fall_Delay ASC LIMIT 1;" ,    
            "SELECT Related_Input_Pin, Fall_Delay FROM Timing_Values WHERE Cell_ID = ( SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = ( SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd' ) ) AND Input_Transition = 0.01 AND Output_Capacitance = 0.0005 ORDER BY Fall_Delay ASC LIMIT 1;"        

        ]
    },
    {
        # min: 0.1031383
        "input": "What is the minimum fall propagation delay for the and2_1 cell in the high density library ? ",
        "view": "Liberty",
        "scl_variant": ['HighDensity'],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins', 'Output_Pins', 'Timing_Values'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT MIN(Fall_Delay) AS Minimum_Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__and2_1' AND Condition_ID = (SELECT Condition_ID  FROM Operating_Conditions  WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd'))"        
        ]
    },
    # #### cross-library comparison 
    {
        # medium speed: 0.1294200000, high speed:  0.1528600000
        "input": "Compare the output pin capacitance of the mux4_1 cell between the high speed and medium speed libraries.",
        "view": "Liberty",
        "scl_variant": ["HighSpeed", "MediumSpeed"],
        "selected_tables": ['Operating_Conditions', 'Cells', 'Output_Pins'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hs') AND Name LIKE 'sky130_fd_sc_hs__mux4_1')) AS High_Speed_Capacitance, (SELECT Max_Capacitance FROM Output_Pins WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_ms') AND Name LIKE 'sky130_fd_sc_ms__mux4_1')) AS Medium_Speed_Capacitance;",
            "SELECT Operating_Conditions.Cell_Library, Output_Pins.Max_Capacitance FROM Output_Pins JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID JOIN Operating_Conditions ON Cells.Condition_ID = Operating_Conditions.Condition_ID WHERE Cells.Name LIKE '%mux4_1' AND Operating_Conditions.Temperature = 25.0 AND Operating_Conditions.Voltage = 1.8 AND Operating_Conditions.Cell_Library IN ('sky130_fd_sc_hs', 'sky130_fd_sc_ms');"
        ]
    },
    {
        # high density: , high density low leakage: 
        # HDLL cell fall: 0.2979633000
        # HD cell fall: 0.2685503
        "input": "Compare the fall propagation delay of the mux2_1 cell between the high density and high density low leakage libraries. Assume an output load of 0.0005 and input rise time of 0.01. Output the fall propagation delay for the timing arc from related input pin named 'S' to the output pin for both libraries.",
        "view": "Liberty",
        "scl_variant": ["HighDensity", "HighDensityLowLeakage"],
        'selected_tables': ['Operating_Conditions', 'Cells', 'Input_Pins', 'Output_Pins', 'Timing_Values'],
        "op_cond": ["Operating Condition with a Temperature of 25 and Voltage of 1.8"],
        "ground_truth": [
            "SELECT (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hd__mux2_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hd')) AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01 AND Related_Input_Pin = 'S') AS HD_Fall_Delay, (SELECT Fall_Delay FROM Timing_Values WHERE Cell_ID = (SELECT Cell_ID FROM Cells WHERE Name = 'sky130_fd_sc_hdll__mux2_1' AND Condition_ID = (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library = 'sky130_fd_sc_hdll')) AND Output_Capacitance = 0.0005 AND Input_Transition = 0.01 AND Related_Input_Pin = 'S') AS HDLL_Fall_Delay",
            "SELECT Cells.Name AS Library, Timing_Values.Fall_Delay FROM Timing_Values JOIN Output_Pins ON Timing_Values.Output_Pin_ID = Output_Pins.Output_Pin_ID JOIN Cells ON Output_Pins.Cell_ID = Cells.Cell_ID WHERE Cells.Name IN ('sky130_fd_sc_hd__mux2_1', 'sky130_fd_sc_hdll__mux2_1') AND Timing_Values.Related_Input_Pin = 'S' AND Timing_Values.Output_Capacitance = 0.0005 AND Timing_Values.Input_Transition = 0.01 AND Cells.Condition_ID IN (SELECT Condition_ID FROM Operating_Conditions WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Library IN ('sky130_fd_sc_hd', 'sky130_fd_sc_hdll'));"     ,
            "SELECT OC.Cell_Library, TV.Fall_Delay FROM Operating_Conditions OC JOIN Cells C ON OC.Condition_ID = C.Condition_ID JOIN Output_Pins OP ON C.Cell_ID = OP.Cell_ID JOIN Timing_Values TV ON C.Cell_ID = TV.Cell_ID AND OP.Output_Pin_ID = TV.Output_Pin_ID WHERE OC.Temperature = 25.0 AND OC.Voltage = 1.8 AND OC.Cell_Library IN ('sky130_fd_sc_hd','sky130_fd_sc_hdll') AND C.Name IN ('sky130_fd_sc_hd__mux2_1','sky130_fd_sc_hdll__mux2_1') AND TV.Related_Input_Pin = 'S' AND TV.Input_Transition = 0.01 AND TV.Output_Capacitance = 0.0005"
        ]
    }
]
    