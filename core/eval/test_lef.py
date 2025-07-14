
test_queries_lef = [
    ### Macro table questions
    {
        # 2.72
        "input": "What is the cell height for the sky130_fd_sc_hd__a2bb2o_1 cell ?",
        "view": "Lef",
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Macros'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_hd__a2bb2o_1'"
        ]
    },
    {
        # 9.66
        "input": "What is the cell width of the sky130_fd_sc_hd__mux4_1 cell ?",
        "view": "Lef",
        'selected_tables': ['Macros'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
            [
                "SELECT Size_Width FROM Macros WHERE name = 'sky130_fd_sc_hd__mux4_1'"
            ]
    },
    {
        # 3.33
        "input": "What is the cell height of the high speed standard cell library ?",
        "view": "Lef",
        'selected_tables': ['Macros'],
        "scl_variant": ["HighSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": 
            [
                "SELECT Size_Height FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hs' LIMIT 1"
            ]
    },
    {
    # sky130_fd_sc_lp__busdriver2_20
    "input": "What is name of the cell with the largest width in the low power library ? ",
    "view": "Lef",
    'selected_tables': ['Macros'],
    "scl_variant": ["LowPower"],
    'op_cond': ['No operating conditions or corners for the LEF view.'],
    "ground_truth":
        [
            "SELECT Name FROM Macros  WHERE Cell_Library = 'sky130_fd_sc_lp' ORDER BY Size_Width DESC LIMIT 1",
            "SELECT Size_Width, Name FROM Macros WHERE Cell_Library = 'sky130_fd_sc_lp' ORDER BY Size_Width DESC LIMIT 1",
            "SELECT Size_Width, Name FROM Macros WHERE Size_Width = (SELECT MAX(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_lp') AND Cell_Library = 'sky130_fd_sc_lp'",
            "SELECT Name, Size_Width FROM Macros WHERE Size_Width = (SELECT MAX(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_lp') AND Cell_Library = 'sky130_fd_sc_lp'",
            "SELECT Name FROM Macros WHERE Size_Width = (SELECT MAX(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_lp') AND Cell_Library = 'sky130_fd_sc_lp'"

        ]
    },
    {
        # sky130_fd_sc_ms__fill_1
        "input": "Which cell has the smallest width in the medium speed library ? ",
        "view": "Lef",
        'selected_tables': ['Macros'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["MediumSpeed"],
        "ground_truth":
        [
            "SELECT Name FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms' ORDER BY Size_Width LIMIT 1",
            "SELECT Name, Size_Width FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms' ORDER BY Size_Width  LIMIT 1",
            "SELECT Size_Width, Name FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms' ORDER BY Size_Width  LIMIT 1",
            "SELECT Name FROM Macros WHERE Size_Width = (SELECT MIN(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms') AND Cell_Library = 'sky130_fd_sc_ms'",
            "SELECT Size_Width, Name FROM Macros WHERE Size_Width = (SELECT MIN(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms') AND Cell_Library = 'sky130_fd_sc_ms'",
            "SELECT Name, Size_Width FROM Macros WHERE Size_Width = (SELECT MIN(Size_Width) FROM Macros WHERE Cell_Library = 'sky130_fd_sc_ms') AND Cell_Library = 'sky130_fd_sc_ms'",

        ]
    },
    {
        "input": "What is the average cell width for each standard cell library?",
        "view": "Lef",
        'selected_tables': ['Macros'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["HighDensity", "HighDensityLowLeakage", "LowSpeed", "HighSpeed", "LowPower", "MediumSpeed"],    
        "ground_truth": [
            "SELECT Cell_Library, AVG(Size_Width) AS Average_Width FROM Macros GROUP BY Cell_Library"
        ]          
    },
    ##pin table questions
    {
        ## A0: 0.126, A1: 0.126, A2: 0.126, A3: 0.126, S0: 0.378, S1: 0.252
        "input": "What is the antenna gate area for all of the sky130_fd_sc_hd__mux4_1 input pins ?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
            [
                "SELECT Antenna_Gate_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__mux4_1') AND Direction = 'INPUT'",
                "SELECT Name, Antenna_Gate_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__mux4_1') AND Direction = 'INPUT'",
                "SELECT p.Pin_ID, p.Name, p.Antenna_Gate_Area FROM Pins p JOIN Macros m ON p.Macro_ID = m.Macro_ID WHERE m.Name ='sky130_fd_sc_hd__mux4_1' AND p.Direction = 'INPUT'; ",
                "SELECT * FROM Pins WHERE Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Name ='sky130_fd_sc_hd__mux4_1' AND Cell_Library ='sky130_fd_sc_hd') AND Direction = 'INPUT' AND Use = 'SIGNAL' AND Antenna_Gate_Area IS NOT NULL;"
            ]
    },
    {
        # X: 0.429
        "input": "What is the antenna diff area for the sky130_fd_sc_hd__mux4_1 macro output pin ?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
            [
                "SELECT Antenna_Diff_Area  FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__mux4_1') AND Direction = 'OUTPUT'",
                "SELECT Name, Antenna_Diff_Area FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__mux4_1') AND Direction = 'OUTPUT'"
            ]
    },
    {
        # VGND VNB VPB VPWR
        "input": "What is the name of the power and ground pins for the sky130_fd_sc_hd__nand2_1 cell in the PDK?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins'],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
        [
            "SELECT Name FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Cell_Library = 'sky130_fd_sc_hd') AND (Use = 'POWER' OR Use = 'GROUND')"
        ]       
    },
    {
        # sky130_fd_sc_hd__o2111ai_4: 4.95
        "input": "Which cell has pins with the largest total antenna gate area, and what is that area in the high density library?",
        "view": "Lef",
        "selected_tables": ['Macros', 'Pins'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Macros.Name AS Cell_Name, SUM(Pins.Antenna_Gate_Area) AS Total_Antenna_Gate_Area FROM Pins JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hd' GROUP BY Macros.Name ORDER BY Total_Antenna_Gate_Area DESC LIMIT 1",
            "SELECT Macros.Name AS Macro, SUM(Pins.Antenna_Gate_Area) AS Total_Antenna_Gate_Area FROM Pins JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hd' GROUP BY Macros.Macro_ID ORDER BY Total_Antenna_Gate_Area DESC LIMIT 1;"
        ]      
    },
    # # pin ports question 
    {
        # li1
        "input": "Which layers are used for drawing the sky130_fd_sc_hd__mux4_1 cell input pin S0  ?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins', 'Pin_Ports'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT pp.Layer FROM Pins p JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE p.Name = 'S0' AND p.Direction = 'INPUT' AND p.Macro_ID IN (SELECT m.Macro_ID FROM Macros m WHERE m.Cell_Library ='sky130_fd_sc_hd' and m.Name='sky130_fd_sc_hd__mux4_1');"
        ]
    },
    {
        # met1, pwell, nwell, met1
        "input": "Which layers are used for the sky130_fd_sc_hdll__nand3b_1 cell power and ground pins ? ",
        "view": "Lef",
        "selected_tables": ['Macros', 'Pins', 'Pin_Ports'],
        "scl_variant": ["HighDensityLowLeakage"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hdll__nand3b_1' AND Cell_Library = 'sky130_fd_sc_hdll') AND Use IN ('POWER', 'GROUND'))"
        ]
    },
    {
        # (sky130_fd_sc_hd__sdfbbn_2', 15.18, 2.72, 41.2896)
        #  (sky130_fd_sc_hd__sedfxbp_2, 15.18, 2.72, 41.2896) # both are correct
        "input": "What is the name, dimensions, and area of the largest cell (by total area) in the high-density library in the PDK that has at least one pin with 'CLOCK' use ?",
        "view": "Lef",
        "selected_tables": ['Macros', 'Pins'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Name, Size_Width, Size_Height, (Size_Width * Size_Height) AS Total_Area FROM Macros WHERE Macro_ID = ( SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd' AND Macro_ID IN (SELECT Macro_ID FROM Pins WHERE Use = 'CLOCK') ORDER BY (Size_Width * Size_Height) DESC LIMIT 1 )",
            "SELECT Macros.Name, Macros.Size_Width, Macros.Size_Height, (Macros.Size_Width * Macros.Size_Height) AS Area FROM Macros JOIN Pins ON Macros.Macro_ID = Pins.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hd' AND Pins.Use = 'CLOCK' GROUP BY Macros.Macro_ID ORDER BY (Macros.Size_Width * Macros.Size_Height) DESC LIMIT 1"
        ]
    },
    {
        # li1, met1
        "input": "Which distinct metal layers are used for drawing the macro clock pins (pins with USE set to 'CLOCK') in the high density library ? ", 
        "view": "Lef",
        'selected_tables': ['Pins', 'Pin_Ports'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT DISTINCT Layer FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Use = 'CLOCK' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd')) "
        ]
    },
    {
        # ('li1', 1257), ('met1', 54)
        "input": "How many input pins in the high density libray are drawn on each layer ?",
        "view": "Lef",
        'selected_tables': ['Pins', 'Pin_Ports'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Layer, COUNT(Pin_ID) AS Input_Pin_Count FROM Pin_Ports WHERE Pin_ID IN (SELECT Pin_ID FROM Pins WHERE Direction = 'INPUT' AND Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd')) GROUP BY Layer"
        ]
    },
    {   # sky130_fd_sc_hdll__probe_p_8, sky130_fd_sc_hdll__probec_p_8
        "input": "List the names of the cells that has pins drawn on the met5 layer in the high density low leakage library in the PDK",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins', 'Pin_Ports'],
        "scl_variant": ["HighDensityLowLeakage"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT DISTINCT m.Name AS Macro_Name FROM Macros m JOIN Pins p ON m.Macro_ID = p.Macro_ID JOIN Pin_Ports pp ON p.Pin_ID = pp.Pin_ID WHERE pp.Layer = 'met5' ORDER BY m.Name;"
        ]
    },
    ## pin port rectangles question
    {
        # X1:0.955, Y1:1.375, X2:1.315 , Y2:1.780
        "input": "Find the rectangle coordinates for the sky130_fd_sc_hs__a2bb2o_2 cell input pin A1_N",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins', 'Pin_Ports', 'Pin_Port_Rectangles'],
        "scl_variant": ["HighSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Rect_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2 FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A1_N' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hs__a2bb2o_2')))",
            "SELECT Rect_X1, Rect_Y1, Rect_X2, Rect_Y2 FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A1_N' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hs__a2bb2o_2')))",
            "SELECT * FROM Pin_Port_Rectangles WHERE Port_ID = (SELECT Port_ID FROM Pin_Ports WHERE Pin_ID = (SELECT Pin_ID FROM Pins WHERE Name = 'A1_N' AND Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hs__a2bb2o_2')))",
        ]
    },
    {
        # sky130_fd_sc_hd__lpflow_clkinvkapwr_16, 6, 22
        "input": "Which cell has the highest number of rectangles per pin in the high density library?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Pins', 'Pin_Ports', 'Pin_Port_Rectangles'],
        "scl_variant": ["HighDensity"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Macros.Name FROM Macros JOIN ( SELECT Pins.Macro_ID, AVG(Rect_Count) AS Avg_Rect_Per_Pin FROM ( SELECT Pin_Ports.Pin_ID, COUNT(Pin_Port_Rectangles.Rect_ID) AS Rect_Count FROM Pin_Port_Rectangles JOIN Pin_Ports ON Pin_Port_Rectangles.Port_ID = Pin_Ports.Port_ID JOIN Pins ON Pin_Ports.Pin_ID = Pins.Pin_ID JOIN Macros ON Pins.Macro_ID = Macros.Macro_ID WHERE Macros.Cell_Library = 'sky130_fd_sc_hd' GROUP BY Pin_Ports.Pin_ID ) AS Rect_Per_Pin JOIN Pins ON Rect_Per_Pin.Pin_ID = Pins.Pin_ID GROUP BY Pins.Macro_ID ) AS Avg_Rect_Per_Pin_Macro ON Macros.Macro_ID = Avg_Rect_Per_Pin_Macro.Macro_ID ORDER BY Avg_Rect_Per_Pin_Macro.Avg_Rect_Per_Pin DESC LIMIT 1",
            "SELECT Macros.Name, (Rect_Count / Pin_Count) AS Rectangles_Per_Pin FROM ( SELECT Pins.Macro_ID, COUNT(Rect_ID) AS Rect_Count FROM Pin_Port_Rectangles JOIN Pin_Ports ON Pin_Port_Rectangles.Port_ID = Pin_Ports.Port_ID JOIN Pins ON Pin_Ports.Pin_ID = Pins.Pin_ID WHERE Pins.Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd') GROUP BY Pins.Macro_ID ) AS Rectangles JOIN ( SELECT Macro_ID, COUNT(Pin_ID) AS Pin_Count FROM Pins WHERE Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd') GROUP BY Macro_ID ) AS Pins ON Rectangles.Macro_ID = Pins.Macro_ID JOIN Macros ON Rectangles.Macro_ID = Macros.Macro_ID ORDER BY Rectangles_Per_Pin DESC LIMIT 1;",
            "SELECT Macros.Name AS Cell_Name, AVG(sub.Rectangles_Count) AS Avg_Rectangles_Per_Pin FROM ( SELECT Pins.Macro_ID, COUNT(Pin_Port_Rectangles.Rect_ID) AS Rectangles_Count FROM Pins JOIN Pin_Ports ON Pins.Pin_ID = Pin_Ports.Pin_ID JOIN Pin_Port_Rectangles ON Pin_Ports.Port_ID = Pin_Port_Rectangles.Port_ID WHERE Pins.Macro_ID IN (SELECT Macro_ID FROM Macros WHERE Cell_Library = 'sky130_fd_sc_hd') GROUP BY Pins.Pin_ID ) AS sub JOIN Macros ON Macros.Macro_ID = sub.Macro_ID GROUP BY Macros.Macro_ID ORDER BY Avg_Rectangles_Per_Pin DESC LIMIT 1"
        ]
    },
    ##### Obstruction questions
    {
        # li1
        "input": "List the name of the obstruction layers in the sky130_fd_sc_ls__a22o_1 cell.",
        "view": "Lef",
        'selected_tables': ['Macros', 'Obstructions'],
        "scl_variant": ["LowSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT Layer FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_ls__a22o_1')"
        ]
    },

    # ##### Obstruction rectangle questions
    # ##### 17
    {
        "input": "How many obstruction rectangles are in the sky130_fd_sc_hs__a21boi_1 cell ?",
        "view": "Lef",
        'selected_tables': ['Macros', 'Obstructions', 'Obstruction_Rectangles'],
        "scl_variant": ["HighSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": [
            "SELECT COUNT(*) AS Num_Obstruction_Rectangles FROM Obstruction_Rectangles WHERE Obstruction_ID IN (SELECT Obstruction_ID FROM Obstructions WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hs__a21boi_1' AND Cell_Library = 'sky130_fd_sc_hs'))",
        ]
    },
    ##### Cross library comparison
    {   
        # HighDensity: 1.380, Medium Speed: 1.44
        "input": "Compare the width of the nand2_1 cell in the High Density and the Medium Speed libraries ",
        "view": "Lef",
        'selected_tables': ['Macros'],
        "scl_variant": ["HighDensity", "MediumSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": 
        [
            "SELECT Size_Width, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' OR Name = 'sky130_fd_sc_ms__nand2_1'",
            "SELECT (SELECT Size_Width FROM Macros WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Cell_Library = 'sky130_fd_sc_hd')) AS Width_HighDensity, (SELECT Size_Width FROM Macros WHERE Macro_ID = (SELECT Macro_ID FROM Macros WHERE Name = 'sky130_fd_sc_ms__nand2_1' AND Cell_Library = 'sky130_fd_sc_ms')) AS Width_MediumSpeed",
            "SELECT Name, Size_Width, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Cell_Library = 'sky130_fd_sc_hd' UNION SELECT Name, Size_Width, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_ms__nand2_1' AND Cell_Library = 'sky130_fd_sc_ms'",
            "SELECT 'High Density' AS Library, Size_Width AS Width FROM Macros WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Cell_Library = 'sky130_fd_sc_hd' UNION SELECT 'Medium Speed' AS Library, Size_Width AS Width FROM Macros WHERE Name = 'sky130_fd_sc_ms__nand2_1' AND Cell_Library = 'sky130_fd_sc_ms';"
        ]
    },
    {   
        # All 3.33
        "input": "Compare the height of the a31oi_1 cell in the High Speed, Low Speed, and Medium Speed libraries ",
        "view": "Lef",
        'selected_tables': ['Macros'],
        "scl_variant": ["HighSpeed", "LowSpeed", "MediumSpeed"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": 
        [
            "SELECT Name, Size_Height FROM Macros WHERE Name IN ('sky130_fd_sc_hs__a31oi_1', 'sky130_fd_sc_ls__a31oi_1', 'sky130_fd_sc_ms__a31oi_1') AND Cell_Library IN ('sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms')",
            "SELECT Name, Size_Height, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND Cell_Library = 'sky130_fd_sc_hs' UNION SELECT Name, Size_Height, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ls' UNION SELECT Name, Size_Height, Cell_Library FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ms'",
            "SELECT 'High Speed' AS Library, Size_Height AS Height FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND Cell_Library = 'sky130_fd_sc_hs' UNION SELECT 'Low Speed' AS Library, Size_Height AS Height FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ls' UNION SELECT 'Medium Speed' AS Library, Size_Height AS Height FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ms'",
            "SELECT (SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_hs__a31oi_1' AND Cell_Library = 'sky130_fd_sc_hs') AS HighSpeedHeight, (SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_ls__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ls') AS LowSpeedHeight, (SELECT Size_Height FROM Macros WHERE Name = 'sky130_fd_sc_ms__a31oi_1' AND Cell_Library = 'sky130_fd_sc_ms') AS MediumSpeedHeight",
            "SELECT Size_Height, Cell_Library FROM Macros WHERE Name IN ('sky130_fd_sc_hs__a31oi_1', 'sky130_fd_sc_ls__a31oi_1', 'sky130_fd_sc_ms__a31oi_1') AND Cell_Library IN ('sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms')"
        ]
    },
    {
        # HighSpeed
        "input": "Which cell library has the smallest width for the mux4_1 cell ?", 
        "view": "Lef",
        "selected_tables": ['Macros'],
        "scl_variant": ["HighDensity", "HighSpeed", "MediumSpeed", "LowSpeed", "LowPower", "HighDensityLowLeakage"],
        'op_cond': ['No operating conditions or corners for the LEF view.'],
        "ground_truth": 
        [
            "SELECT Cell_Library FROM Macros WHERE Name LIKE '%__mux4_1' ORDER BY Size_Width ASC LIMIT 1",
            "SELECT Cell_Library, MIN(Size_Width) AS SmallestWidth FROM Macros WHERE Name LIKE 'sky130_fd_sc_%__mux4_1' GROUP BY Cell_Library ORDER BY SmallestWidth ASC LIMIT 1",
            "SELECT Cell_Library FROM ( SELECT Cell_Library, MIN(Size_Width) AS MinWidth FROM Macros WHERE Name LIKE '%__mux4_1' GROUP BY Cell_Library ) AS SubQuery ORDER BY MinWidth ASC LIMIT 1",
            "SELECT Cell_Library, Size_Width FROM Macros WHERE Name LIKE '%__mux4_1' ORDER BY Size_Width ASC LIMIT 1",
            "SELECT Cell_Library, Size_Width FROM Macros WHERE Name LIKE '%mux4_1%' AND Size_Width = (SELECT MIN(Size_Width) FROM Macros WHERE Name LIKE '%mux4_1%')",
            "SELECT Cell_Library FROM Macros WHERE Name LIKE '%__mux4_1' AND Size_Width = (SELECT MIN(Size_Width) FROM Macros WHERE Name LIKE '%__mux4_1')"
        ]
    }
]