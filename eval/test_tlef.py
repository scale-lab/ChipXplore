
test_queries_tlef = [
    # #### cross-corner comparisons
    {
        # min: 0.105, max: 0.145, nom: 0.125
        "input": "Compare the resistance per square unit of the met1 routing layer the between the three corners: nom, min, max",
        "view": "TechnologyLef",
        'op_cond': ['nom', 'min', 'max'],
        'selected_tables': ['Routing_Layers'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
            [
                "SELECT Resistance_Per_SQ FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('nom', 'min', 'max')",
                "SELECT Corner, Resistance_Per_SQ FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('nom', 'min', 'max');",
                "SELECT Resistance_Per_SQ, Corner FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('nom', 'min', 'max');"
            ]
    },  
    {
        # min: 0.5, max: 8.0
        "input": "Compare the resistance of the via2 cut layer between the two operating corners: min, max",
        "view": "TechnologyLef",
        'op_cond': ['min', 'max'],
        'selected_tables': ['Cut_Layers'],
        "scl_variant": ["HighDensity"],
        "ground_truth": 
            [
                "SELECT Resistance FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('min', 'max')",
                "SELECT Corner, Resistance FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('min', 'max');",
                "SELECT Resistance, Corner FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner IN ('min', 'max');",
                "SELECT (SELECT Resistance FROM Cut_Layers WHERE Layer_ID = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'min')) AS Resistance_Min, (SELECT Resistance FROM Cut_Layers WHERE Layer_ID = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'max')) AS Resistance_Max;",
                "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID  = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd')"
            ]
    }, 
    ## cross library comparisons
    {
        # HS: 3.33, HD: 3.4
        "input": "Compare the pitch values for the met5 layer between the high density and high speed libraries for the nominal corner",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        'selected_tables': ['Routing_Layers'],
        "scl_variant": ["HighDensity", 'HighSpeed'],
        "ground_truth": 
            [
                "SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hd' UNION SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs'",
                "SELECT Cell_Library, Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND (Cell_Library = 'sky130_fd_sc_hd' OR Cell_Library = 'sky130_fd_sc_hs') AND Corner = 'nom'",
                "SELECT Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library IN ('sky130_fd_sc_hd', 'sky130_fd_sc_hs') AND Corner = 'nom'",
                "SELECT (SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs' AND Corner = 'nom') AS High_Speed_Library_Pitch, (SELECT Pitch_X FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom') AS High_Density_Library_Pitch",
                "SELECT * FROM (SELECT Pitch_X AS Pitch_HighDensity FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom') AS HD, (SELECT Pitch_X AS Pitch_HighSpeed FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs' AND Corner = 'nom') AS HS",
                "SELECT hd.Pitch_X AS HD_Pitch_X, hd.Pitch_Y AS HD_Pitch_Y, hs.Pitch_X AS HS_Pitch_X, hs.Pitch_Y AS HS_Pitch_Y FROM (SELECT Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom') AS hd JOIN (SELECT Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs' AND Corner = 'nom') AS hs;",
                "SELECT 'High Density' AS Library, Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' UNION SELECT 'High Speed' AS Library, Pitch_X, Pitch_Y FROM Routing_Layers WHERE Name = 'met5' AND Cell_Library = 'sky130_fd_sc_hs' AND Corner = 'nom'"
            ]
    },
    # Routing Layers questions
    {
        # 0.14
        "input": "What is the width of the metal 1 layer?",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": 
            [
                "SELECT Width FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'",
                "SELECT Name, Width FROM Routing_Layers WHERE Name = 'met1' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'"
            ]
    },
    {
        # 6
        "input": "Count the number of routing layers in this PDK.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": 
            [
                "SELECT COUNT(*) FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'"
            ]
    },
    {
        # li1, met1, met2, met3, met4, met5
        "input": "List the names for the routing layers in this PDK.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": 
            [
                "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'"
            ]
    },
    {
        # met5 (1.2), met3 (0.8), met4 (0.8), met1 (0.35), met2 (0.35), li1 (0.1)
        "input": "List all the routing layers in the PDK with the thickest layer first.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": [
            "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Thickness DESC;",
            "SELECT Name, Thickness FROM Routing_Layers WHERE Type = 'ROUTING' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Thickness DESC",
               "SELECT * FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Thickness DESC;",
            'SELECT r."Layer_ID", r."Name", r."Thickness" FROM "Routing_Layers" r WHERE r."Cell_Library" = "sky130_fd_sc_hd" AND r."Corner" = "nom" ORDER BY r."Thickness" DESC;'
        ]
    },
    {
        # li1, met2, met4
        "input": "List the name of the routing layers with direction set to vertical.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": [
            "SELECT Name FROM Routing_Layers WHERE Type = 'ROUTING' AND Direction = 'VERTICAL' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom';",
            "SELECT Name, Layer_ID FROM Routing_Layers WHERE Type = 'ROUTING' AND Direction = 'VERTICAL' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd'"
        ]
    },
    {
        # met5 (1.6), met3 (0.3), met4 (0.4), li1 (0.17), met1 (0.14), met2 (0.14)
        "input": "List all the routing layers in the PDK with the largest width first.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers'],
        "ground_truth": 
            [
                "SELECT Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Width DESC",
                "SELECT Layer_ID, Name FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Width DESC",
                "SELECT Name, Width FROM Routing_Layers WHERE Type = 'ROUTING' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Width DESC",
                "SELECT Width, Name FROM Routing_Layers WHERE Type = 'ROUTING' AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Width DESC",
                "SELECT * FROM Routing_Layers WHERE Cell_Library ='sky130_fd_sc_hd' AND Corner = 'nom' ORDER BY Width DESC;"
            ]
    },
    {
        # (0.0, 400.0)	(0.0125, 400.0)	(0.0225, 2609.0) (22.5, 11600.0)
        "input": "What are the coordinates for the antenna differential side area ratios for the met1 routing layer ? ",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Routing_Layers', 'Antenna_Diff_Side_Area_Ratios'],
        "ground_truth": 
            [
                "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID = (SELECT Layer_ID FROM Routing_Layers WHERE Name = 'met1' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd')",
                "SELECT Ratio_ID, X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID = (SELECT Layer_ID FROM Routing_Layers WHERE Name = 'met1' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd')"
            ]
    },
    {
        "input": "What is the antenna diff side area ratio for each routing layer in the nom corner ?",
        "view": "TechnologyLef",
        "op_cond": ['nom'],
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Routing_Layers', 'Antenna_Diff_Side_Area_Ratios'],
        "ground_truth": [
            "SELECT r.Name, a.X1, a.Y1, a.X2, a.Y2, a.X3, a.Y3, a.X4, a.Y4 FROM Routing_Layers r JOIN Antenna_Diff_Side_Area_Ratios a ON r.Layer_ID = a.Routing_Layer_ID WHERE r.Cell_Library = 'sky130_fd_sc_hd' AND r.Corner = 'nom'",
            "SELECT r.Name, a.Type, a.X1, a.Y1, a.X2, a.Y2, a.X3, a.Y3, a.X4, a.Y4 FROM Routing_Layers r JOIN Antenna_Diff_Side_Area_Ratios a ON r.Layer_ID = a.Routing_Layer_ID WHERE r.Cell_Library = 'sky130_fd_sc_hd' AND r.Corner = 'nom'"
        ]
    },
    {
        "input": "Average Pitch in X and Y by Layer Direction",
        "view": "TechnologyLef",
        "op_cond": ['nom'],
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Routing_Layers'],
        "ground_truth": [
            "SELECT Direction, AVG(Pitch_X) as Avg_Pitch_X, AVG(Pitch_Y) as Avg_Pitch_Y FROM Routing_Layers GROUP BY Direction",
            "SELECT Direction, AVG(Pitch_X) AS Avg_Pitch_X, AVG(Pitch_Y) AS Avg_Pitch_Y FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' GROUP BY Direction",
        ]
    },
    {
        # For the 'max' corner, the average resistance per square is approximately 2.9063.
        #- For the 'min' corner, the average resistance per square is approximately 1.5845.
        #- For the 'nom' (nominal) corner, the average resistance per square is approximately 2.1954.
        "input": "What is the average resistance per square for routing layers by corner, consider all operating corners ?",
        "view": "TechnologyLef",
        "op_cond": ['nom', 'min', 'max'],
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Routing_Layers'],
        "ground_truth": [
           "SELECT Corner, AVG(Resistance_Per_SQ) AS Average_Resistance_Per_SQ FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' GROUP BY Corner;",
           "SELECT Corner, AVG(Resistance_Per_SQ) AS Avg_Resistance_Per_SQ FROM Routing_Layers WHERE Cell_Library IN ('sky130_fd_sc_hd', 'sky130_fd_sc_hdll', 'sky130_fd_sc_hs', 'sky130_fd_sc_ls', 'sky130_fd_sc_ms', 'sky130_fd_sc_lp') AND Corner IN ('min', 'nom', 'max') GROUP BY Corner;"
        ]
    },
    {
        "input": "Average AC current density values for routing layers in the PDK by direction",
        "view": "TechnologyLef",
        "op_cond": ['nom'],
        "scl_variant": ["HighDensity"],
        "selected_tables": ['Routing_Layers'],
        "ground_truth": [
           " SELECT Direction, AVG(AC_Current_Density_Rms) as Average_AC_Current_Density FROM Routing_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' GROUP BY Direction; "
        ]
    },
    # ### Cut Layer questions
    {
        # 5
        "input": "What is the number of cut layers in this PDK ?",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Cut_Layers'],
        "ground_truth": 
            [
                "SELECT COUNT(*) FROM Cut_Layers WHERE Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd'"
            ]
    },
    {
        # (0.0, 6.0) (0.0125, 6.0) (0.0225, 6.81) (22.5, 816.0)
        "input": "What is the antenna area ratio for via2 cut layer ? ",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Cut_Layers', 'Antenna_Diff_Area_Ratios'],
        "ground_truth": 
            [
                "SELECT X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID  = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd')",
                "SELECT Ratio_ID, X1, Y1, X2, Y2, X3, Y3, X4, Y4 FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID = (SELECT Layer_ID FROM Cut_Layers WHERE Name = 'via2' AND Corner = 'nom' AND Cell_Library = 'sky130_fd_sc_hd')",
                'SELECT * FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID = (SELECT Layer_ID FROM Cut_Layers WHERE Name = "via2" AND Corner = "nom" AND Cell_Library = "sky130_fd_sc_hd")'
            ]
    },
    {
        # L1M1_PR, L1M1_PR_R, L1M1_PR_M, L1M1_PR_MR, L1M1_PR_C 
        "input": "List the via names that have mcon layer.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        'selected_tables': ['Vias', 'Via_Layers'],
        "scl_variant": ["HighDensity"],
        "ground_truth": [
            "SELECT Name FROM Vias WHERE Via_ID IN (SELECT Via_ID FROM Via_Layers WHERE Layer_Name = 'mcon') AND Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom'"
        ]
    },
    {
        "input": "For each cut layer in the 'nom' corner, List the layer name and its associated antenna diff area ratio values?",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Cut_Layers', 'Antenna_Diff_Area_Ratios'],
        "ground_truth": [
            "SELECT Cut_Layers.Name, Antenna_Diff_Area_Ratios.X1, Antenna_Diff_Area_Ratios.Y1, Antenna_Diff_Area_Ratios.X2, Antenna_Diff_Area_Ratios.Y2, Antenna_Diff_Area_Ratios.X3, Antenna_Diff_Area_Ratios.Y3, Antenna_Diff_Area_Ratios.X4, Antenna_Diff_Area_Ratios.Y4 FROM Cut_Layers JOIN Antenna_Diff_Area_Ratios ON Cut_Layers.Layer_ID = Antenna_Diff_Area_Ratios.Cut_Layer_ID WHERE Cut_Layers.Cell_Library = 'sky130_fd_sc_hd' AND Cut_Layers.Corner = 'nom'"
        ]
    },
    {
        "input": "Calculate the average resistance for cut layers in each corner in the PDK",
        "view": "TechnologyLef",
        'op_cond': ['nom', 'min', 'max'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Cut_Layers'],
        "ground_truth": [
            "SELECT Corner, AVG(Resistance) AS Average_Resistance FROM Cut_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' GROUP BY Corner"
        ]
    },
    {
        "input": "Calculate the average current density for cut layers in each corner",
        "view": "TechnologyLef",
        'op_cond': ['nom', 'min', 'max'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Cut_Layers'],
        "ground_truth": [
            "SELECT Corner, AVG(DC_Current_Density) AS Average_DC_Current FROM Cut_Layers WHERE Cell_Library = 'sky130_fd_sc_hd' GROUP BY Corner"
        ]
    },
    # ## Via Layers question 
    {
        "input": "How many via configurations have an upper metal layer set to met5 ?",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Vias'],
        "ground_truth": [
            "SELECT COUNT(*) FROM Vias WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' AND Upper_Layer = 'met5';"
        ]
    },
    {
        "input": "What are the layer names associated with via named M1M2_PR ?",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Vias', 'Via_Layers'],
        "ground_truth": [
            "SELECT vl.Layer_Name FROM Via_Layers vl JOIN Vias v ON vl.Via_ID = v.Via_ID WHERE v.Name = 'M1M2_PR' AND v.Cell_Library = 'sky130_fd_sc_hd' AND v.Corner = 'nom'"
        ]
    },
    {
        "input": "Count the number of vias in the PDK for each combination of upper and lower layers.",
        "view": "TechnologyLef",
        'op_cond': ['nom'],
        "scl_variant": ["HighDensity"],
        'selected_tables': ['Vias', 'Via_Layers'],
        "ground_truth": [
            "SELECT Upper_Layer, Lower_Layer, COUNT(*) AS Via_Count FROM Vias WHERE Cell_Library = 'sky130_fd_sc_hd' AND Corner = 'nom' GROUP BY Upper_Layer, Lower_Layer;"
        ]
    }
]