""""Convert Lef file to SQL database
"""

import os 
import re
import sys
import tqdm
import sqlite3
import argparse

from config.pdks import get_scl, get_techlef_paths, get_techlef_corners
from core.parsers.lef.lef_parser import LefParser
from core.database.db_utils import delete_database


def parse_via_name(via_name):
    routing_layers = {
        'L1': 'li1',
        'M1': 'met1', 
        'M2': 'met2',
        'M3': 'met3',
        'M4': 'met4',
        'M5': 'met5'
    }
    parts = via_name.split('_')
    
    metal_layers = parts[0]
    
    layers = re.findall(r'[ML]\d+', metal_layers)
    
    if len(layers) != 2:
        # raise ValueError(f"Expected two metal layers, found {len(layers)} in {via_name}")
        return {
            'lower_layer': None,
            'upper_layer': None 
        }
    return {
        'lower_layer': routing_layers[layers[0]],
        'upper_layer': routing_layers[layers[1]]
    }

    
def insert_tlef_data(conn, layer_dict, via_dict, corner, scl_variant):
    
    cursor = conn.cursor()

    # insert_via_data(cursor, via_dict)
    for _, layer in layer_dict.items():
        
        layer_type = layer.layer_type
        if layer_type == "ROUTING": 
            
            capacitance_per_sq_dst = None 
            if layer.capacitance: 
                capacitance_per_sq_dst = layer.capacitance[1]

            resistance_per_sq = None 
            if layer.resistance : 
                resistance_per_sq = layer.resistance if isinstance(layer.resistance, float) else layer.resistance[1]
      
            # dc_current_density = None 
            dc_current_density =  layer.dc_current_density[1] if layer.dc_current_density else None
            ac_current_density = layer.ac_current_density[1] if layer.ac_current_density else None

            if layer.offset: 
                offset_x = float(layer.offset[0]) if isinstance(layer.offset, tuple) else float(layer.offset)
                offset_y = float(layer.offset[1]) if isinstance(layer.offset, tuple) else float(layer.offset)
            else:
                offset_x = None 
                offset_y = None 
                
            if layer.pitch: 
                pitch_x = float(layer.pitch[0]) if isinstance(layer.pitch, tuple) else float(layer.pitch)
                pitch_y = float(layer.pitch[0]) if isinstance(layer.pitch, tuple) else float(layer.pitch)
            else:
                pitch_x = None 
                pitch_y = None 
                
            density_check_window_x = layer.density_check_window[0]  if layer.density_check_window  else None 
            density_check_window_y = layer.density_check_window[1] if layer.density_check_window  else None 
            
            min_enclosed_area = layer.min_enclosed_area
            antenna_model = layer.antenna_model
            antenna_diff_side_area = layer.antenna_diff_side_area_ratio
            
            # Insert layers and properties (simplified)
            cursor.execute('''
                INSERT INTO Routing_Layers (Name, Type, Direction, Pitch_X, Pitch_Y, Offset_X, Offset_Y, Width, Spacing, Area, Thickness, Min_Enclosed_Area, Edge_Capacitance, Capacitance_Per_SQ_Dist, Resistance_Per_SQ, DC_Current_Density_Avg, AC_Current_Density_Rms, Maximum_Density, Density_Check_Window_X, Density_Check_Window_Y, Density_Check_Step, Antenna_Model, Corner, Cell_Library)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (layer.name, layer.layer_type, layer.direction, pitch_x, pitch_y, offset_x, offset_y, layer.width, layer.spacing,
                  layer.area, layer.thickness, min_enclosed_area, layer.edge_cap, capacitance_per_sq_dst, resistance_per_sq,dc_current_density, ac_current_density, layer.max_density, density_check_window_x, density_check_window_y, layer.density_check_step, antenna_model,
                  corner, scl_variant))
                        
            layer_id = cursor.lastrowid

            antenna_diff_side_area_type = None 
            if antenna_diff_side_area: 
                antenna_diff_side_area_type = antenna_diff_side_area[0]
           
                cursor.execute('''
                    INSERT INTO Antenna_Diff_Side_Area_Ratios (Routing_Layer_ID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4) 
                    VALUES (?, ?, ?, ?, ?, ? , ?, ?, ?, ?) 
                    ''', 
                    (layer_id, antenna_diff_side_area_type, antenna_diff_side_area[1][0], antenna_diff_side_area[1][1], 
                    antenna_diff_side_area[2][0], antenna_diff_side_area[2][1], antenna_diff_side_area[3][0], antenna_diff_side_area[3][1],
                    antenna_diff_side_area[4][0], antenna_diff_side_area[4][1])
                )

        elif layer_type == "CUT": 

            dc_current_density =  layer.dc_current_density[1] if layer.dc_current_density else None

            enclosure_below_x= None 
            enclosure_below_y = None 
            enclosure_above_x = None
            enclosure_above_y = None 
            for enclosure in layer.enclosures:
                if enclosure[0] == 'BELOW': 
                    enclosure_below_x = enclosure[1]
                    enclosure_below_y = enclosure[2]
                if enclosure[0] == 'ABOVE':
                    enclosure_above_x = enclosure[1]
                    enclosure_above_y = enclosure[2]
            
            
            antenna_diff_area_ratio = layer.antenna_diff_area_ratio if layer.antenna_diff_area_ratio else None
            cursor.execute('''
            INSERT INTO Cut_Layers (Name, Type, Width, Spacing, Enclosure_Below_X, Enclosure_Below_Y, Enclosure_Above_X, Enclosure_Above_Y, Resistance, DC_Current_Density, Corner, Cell_Library
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            
            ''', (layer.name, layer.layer_type, layer.width, layer.spacing, enclosure_below_x, enclosure_below_y, enclosure_above_x, enclosure_above_y, layer.resistance, dc_current_density, corner, scl_variant))

            
            layer_id = cursor.lastrowid

            if antenna_diff_area_ratio: 
                antenna_diff_area_type = antenna_diff_area_ratio[0]
                cursor.execute('''
                    INSERT INTO Antenna_Diff_Area_Ratios (Cut_Layer_ID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4) 
                    VALUES (?, ?, ?, ?, ?, ? , ?, ?, ?, ?) 
                    ''', 
                    (layer_id, antenna_diff_area_type, antenna_diff_area_ratio[1][0], antenna_diff_area_ratio[1][1], 
                    antenna_diff_area_ratio[2][0], antenna_diff_area_ratio[2][1], antenna_diff_area_ratio[3][0], antenna_diff_area_ratio[3][1],
                    antenna_diff_area_ratio[4][0], antenna_diff_area_ratio[4][1])
                )


    # Insert via data
    for _, via in via_dict.items():
        via_name = via.name     
        metal_layers = parse_via_name(via_name)
        lower_layer = metal_layers['lower_layer']
        upper_layer =  metal_layers['upper_layer']
        cursor.execute('''
            INSERT INTO VIAS (Name, Corner, Lower_Layer, Upper_Layer, Cell_Library) VALUES (?, ?, ?, ?, ?)
        ''', (via_name,corner, lower_layer, upper_layer, scl_variant))
        via_id = cursor.lastrowid
        for layer in via.layers:            
            cursor.execute('''
                INSERT INTO Via_Layers (Via_ID, Layer_Name, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (via_id, layer.name, layer.shapes[0].points[0][0], layer.shapes[0].points[0][1], layer.shapes[0].points[1][0], layer.shapes[0].points[1][1]))

    conn.commit()
    
    
def get_tlef_description(selected_schema=None, partition=False):
    routing_layers_table = """
# Table: Routing_Layers
Stores properties of routing layers including their name, type, geometrical dimensions, and electrical properties.
Routing layers typically refer to metal layers.
[
    (Layer_ID, the unique identifier of the layer. Value examples: [101, 102, 103, 104]),
    (Name, the name of the layer. Value examples: ['li1', 'met1', 'met2']),
    (Type, the type of the layer, typically 'ROUTING'.),
    (Direction, the preferred routing direction of the layer, either horizontal or vertical. Value examples: ['VERTICAL', 'HORIZONTAL']),
    (Pitch_X, Pitch_Y, describes the pitch in X and Y directions. Value examples: [0.46, 0.34]),
    (Offset_X, Offset_Y, describes the offset in X and Y directions. Value examples: [0.23, 0.17]),
    (Width, the width of the routing path. Value examples: [0.17]),
    (Spacing, the spacing between routing paths. Value examples: [0.17]),
    (Area, the area of the layer. Value examples: [0.0561]),
    (Thickness, the thickness of the layer. Value examples: [0.1]),
    (Min_Enclosed_Area, the minimum enclosed area of the layer. Value examples: [0.14]),
    (Edge_Capacitance, the edge capacitance per unit length. Value examples: [40.697E-6]),
    (Capacitance_Per_SQ_Dist, capacitance per square distance. Value examples: [36.9866E-6]),
    (Resistance_Per_SQ, resistance per square unit. Value examples: [12.8]),
    (DC_Current_Density_Avg, the average DC current density. Value examples: [2.8]),
    (AC_Current_Density_Rms, the RMS AC current density. Value examples: [6.1]),
    (Maximum_Density, the maximum density allowed. Value examples: [70]),
    (Density_Check_Window_X, DensityCheckWindowY, the dimensions of the density check window. Value examples: [700, 700]),
    (Density_Check_Step, the step size for density checks. Value examples: [70]),
    (Antenna_Model, the model of the antenna effect considered. Value examples: ['OXIDE1']),
"""

    if partition: 
        routing_layers_table += """
]
"""
    else:
        routing_layers_table += """
    (Cell_Library, standard cell library variant. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls])
    (Corner, operating corner for this layer entry. Value examples: [min, nom, max])
]
"""

    antenna_diff_side_area_ratios_table = """
# Table: Antenna_Diff_Side_Area_Ratios
Contains the piecewise linear (PWL) antenna differential side area ratios for each routing layer.
[
    (Ratio_ID, the unique identifier of the ratio entry.),
    (Routing_Layer_ID, references the associated layer in RoutingLayers.),
    (Type, the type of antenna model used, usually 'OXIDE1'.),
    (X1, Y1, X2, Y2, X3, Y3, X4, Y4, the coordinates of the PWL function describing the antenna effect. Examples: [(0, 75), (0.0125, 75), (0.0225, 85.125), (22.5, 10200)]),
]
"""

    cut_layers_table = """
# Table: Cut_Layers
Stores properties of cut layers including their dimensions and electrical properties.
Cut layers typically refer to the via layers.
[
    (LayerID, the unique identifier of the cut layer.),
    (Name, the name of the cut layer. Value examples: ['via', 'mcon']),
    (Type, the type of the layer, typically 'CUT'.),
    (Width, the width of the cut. Value examples: [0.15]),
    (Spacing, the spacing between cuts. Value examples: [0.17]),
    (Enclosure_Below_X, Enclosure_Below_Y, the enclosure dimensions below the cut. Value examples: [0.055, 0.085]),
    (Enclosure_Above_X, Enclosure_Above_Y, the enclosure dimensions above the cut. Value examples: [0.055, 0.085]),
    (Resistance, the resistance of the cut layer. Value examples: [4.5]),
    (DC_Current_Density, the DC current density. Value examples: [0.29]),
    (Cell_Library, standard cell library variant. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls]),
    (Corner, operating corner for this specific layer entry. Value examples: [min, nom, max])  
]
"""

    if partition: 
        cut_layers_table += """
]
""" 
    else:
        cut_layers_table += """
    (Cell_Library, standard cell library variant. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls]),
    (Corner, operating corner for this specific layer entry. Value examples: [min, nom, max])  
]
"""

    antenna_diff_area_ratios_table = """
# Table: Antenna_Diff_Area_Ratios
Contains the piecewise linear (PWL) antenna differential area ratios for each cut layer.
[
    (Ratio_ID, the unique identifier of the ratio entry.),
    (Cut_Layer_ID, references the associated layer in CutLayers.),
    (Type, the type of antenna model used, typically 'OXIDE1'.),
    (X1, Y1, X2, Y2, X3, Y3, X4, Y4, the coordinates of the PWL function describing the antenna effect. Examples: [(0, 6), (0.0125, 6), (0.0225, 6.81), (22.5, 816)])
]
    """

    vias_table = """
# Table: Vias
Stores basic information about vias used in the technology.
[
    (Via_ID, the unique identifier of the via. value examples: [1, 2, 3]),
    (Name, the name of the via, such as 'L1M1_PR'.),
    (Lower_Layer, the name of the lower metal layer. Value examples: ['li1', 'met1', 'met3'])
    (Upper_Layer, the name of the upper metal layer. Value examples: ['met1', 'met2', 'met4'])
"""
    if partition:
        vias_table += """
]
"""
    else:
        vias_table += """
    (Cell_Library, standard cell library variant. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls]),
    (Corner, operating corner for this via entry. Value examples: [min, nom, max])  
]
"""

    via_layers_table = """
# Table: Via_Layers
Stores details about the layers involved in each via, including their geometrical dimensions.
[
    (Via_Layer_ID, the unique identifier of the via layer entry.),
    (Via_ID, references the associated via in Vias.),
    (Layer_Name, the name of the layer involved. Value examples: ['mcon', 'li1', 'met1']),
    (Rect_X1, Rect_Y1, Rect_X2, Rect_Y2, the coordinates defining the rectangle of the via on the layer.),
]
    """

    description = """The Technolog LEF database contains information about the different standard cell libraries for three different corners (min, nom, max). It has the following tables:  \n"""

    if selected_schema: 
        if 'Routing_Layers' in selected_schema:
            description += routing_layers_table
            
        if 'Antenna_Diff_Side_Area_Ratios'  in selected_schema:
            description += antenna_diff_side_area_ratios_table
        
        if 'Cut_Layers'  in selected_schema:
            description += cut_layers_table
        
        if 'Antenna_Diff_Area_Ratios'  in selected_schema:
            description += antenna_diff_area_ratios_table
        
        if 'Vias' in selected_schema:
            description += vias_table

        if 'Via_Layers' in selected_schema:
            description += via_layers_table
            
    else:
        # Build the complete description
        description = routing_layers_table + antenna_diff_side_area_ratios_table + cut_layers_table + antenna_diff_area_ratios_table + vias_table + via_layers_table
        
    return description


def get_compact_tlef_description(selected_schema=None):
    """Returns a compact description of the tables in the selected Technology LEF schema"""
    
    routing_layers_table = """
## RoutingLayers
Properties of routing (metal) layers.
- Columns: LayerID, Name, Type, Direction, PitchX, PitchY, OffsetX, OffsetY, Width, Spacing, Area, Thickness, MinEnclosedArea, EdgeCapacitance, CapacitancePerSQDist, ResistancePerSQ, DCCurrentDensityAvg, ACCurrentDensityRms, MaximumDensity, DensityCheckWindowX, DensityCheckWindowY, DensityCheckStep, AntennaModel, Cell_Library, Corner
"""

    antenna_diff_side_area_ratios_table = """
## AntennaDiffSideAreaRatios
Piecewise linear antenna differential side area ratios for routing layers.
- Columns: RatioID, RoutingLayerID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4
"""

    cut_layers_table = """
## CutLayers
Properties of cut (via) layers.
- Columns: LayerID, Name, Type, Width, Spacing, EnclosureBelowX, EnclosureBelowY, EnclosureAboveX, EnclosureAboveY, Resistance, DCCurrentDensity, Cell_Library, Corner
"""

    antenna_diff_area_ratios_table = """
## AntennaDiffAreaRatios
Piecewise linear antenna differential area ratios for cut layers.
- Columns: RatioID, CutLayerID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4
"""

    vias_table = """
## Vias
Basic information about vias.
- Columns: Via_ID, Name, Cell_Library, Corner
"""

    via_layers_table = """
## Via_Layers
Details about layers involved in each via.
- Columns: Via_Layer_ID, Via_ID, Layer_Name, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2
"""
    
    desc = "# Technology LEF Database Tables\n"

    if selected_schema: 
        if 'Routing_Layers' in selected_schema:
            desc += routing_layers_table
        if 'Antenna_Diff_Side_Area_Ratios' in selected_schema:
            desc += antenna_diff_side_area_ratios_table
        if 'Cut_Layers' in selected_schema:
            desc += cut_layers_table
        if 'Antenna_Diff_Area_Ratios' in selected_schema:
            desc += antenna_diff_area_ratios_table
        if 'Vias' in selected_schema:
            desc += vias_table
        if 'Via_Layers' in selected_schema:
            desc += via_layers_table
    else:
        desc += routing_layers_table + antenna_diff_side_area_ratios_table + cut_layers_table + antenna_diff_area_ratios_table + vias_table + via_layers_table
         
    return desc.strip()

def get_tlef_foreign_keys(selected_schema):
    
    routing_layer_antenna_ratio = "Routing_Layers.`Layer_ID` = Antenna_Diff_Side_Area_Ratios.`Layer_ID` \n"
    cut_layer_antenna_ratio = "Cut_Layers.`Layer_ID` = Antenna_Diff_Area_Ratios.`Layer_ID` \n"
    via_layer_id = "Vias.`Via_ID` = Via_Layers.`Via_ID` \n"
    
    fk_str = ""
    if selected_schema != None: 
        if set(['Routing_Layers', 'Antenna_Diff_Side_Area_Ratios']).issubset(set(selected_schema)):
            fk_str += routing_layer_antenna_ratio

        if set(['Cut_Layers', 'Antenna_Diff_Area_Ratios']).issubset(set(selected_schema)):
            fk_str += cut_layer_antenna_ratio
        
        if set(['Vias', 'Via_Layers']).issubset(set(selected_schema)):
            fk_str += via_layer_id
    else: 
        fk_str = """
RoutingLayers.`Layer_ID` = Antenna_Diff_Side_Area_Ratios.`Layer_ID` 
Cut_Layers.`Layer_ID` = Antenna_Diff_Area_Ratios.`Layer_ID`
Vias.`Via_ID` = Via_Layers.`Via_ID`
"""
    
    return fk_str


def create_tlef_tables(conn):
    
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Routing_Layers (
        Layer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Type TEXT,
        Direction TEXT,
        Pitch_X REAL,
        Pitch_Y REAL,
        Offset_X REAL,
        Offset_Y REAL,
        Width REAL,
        Spacing REAL,
        Area REAL,
        Thickness REAL,
        Min_Enclosed_Area REAL,
        Edge_Capacitance REAL,
        Capacitance_Per_SQ_Dist REAL,
        Resistance_Per_SQ REAL,
        DC_Current_Density_Avg REAL,
        AC_Current_Density_Rms REAL,
        Maximum_Density REAL,
        Density_Check_Window_X REAL,
        Density_Check_Window_Y REAL,
        Density_Check_Step REAL,
        Antenna_Model TEXT,
        Corner TEXT,  --Corner column
        Cell_Library TEXT  -- Cell library column
    );
    ''')
    
    cursor.execute(
    '''
     CREATE TABLE IF NOT EXISTS Antenna_Diff_Side_Area_Ratios (
        Ratio_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Routing_Layer_ID INTEGER,
        Type TEXT,
        X1 REAL, Y1 REAL,
        X2 REAL, Y2 REAL,
        X3 REAL, Y3 REAL,
        X4 REAL, Y4 REAL,
        FOREIGN KEY (Routing_Layer_ID) REFERENCES Routing_Layers(Layer_ID)
    );
    '''    
    )
    
       
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cut_Layers (
        Layer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Type TEXT,
        Width REAL,
        Spacing REAL,
        Enclosure_Below_X REAL,
        Enclosure_Below_Y REAL,
        Enclosure_Above_X REAL,
        Enclosure_Above_Y REAL,
        Resistance REAL,
        DC_Current_Density REAL,
        Corner TEXT,  --Corner column
        Cell_Library TEXT  -- Cell Variant column
    );      
    ''')
    
    cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS Antenna_Diff_Area_Ratios (
        Ratio_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Cut_Layer_ID INTEGER,
        Type TEXT,
        X1 REAL, Y1 REAL,
        X2 REAL, Y2 REAL,
        X3 REAL, Y3 REAL,
        X4 REAL, Y4 REAL,
        FOREIGN KEY (Cut_Layer_ID) REFERENCES Cut_Layers(Layer_ID)
    );
    '''    
    )
       
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS Vias (
            Via_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Upper_Layer TEXT,
            Lower_Layer TEXT,
            Corner TEXT,
            Cell_Library TEXT
        );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Via_Layers (
        Via_Layer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Via_ID INTEGER,
        Layer_Name TEXT,
        Rect_X1 REAL,
        Rect_Y1 REAL,
        Rect_X2 REAL,
        Rect_Y2 REAL,
        FOREIGN KEY (Via_ID) REFERENCES Vias(Via_ID)
    );
    ''') 

    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_routing_layer_id ON Antenna_Diff_Side_Area_Ratios (Routing_Layer_ID);",
        "CREATE INDEX IF NOT EXISTS idx_cut_layer_id ON Antenna_Diff_Area_Ratios (Cut_Layer_ID);",
        "CREATE INDEX IF NOT EXISTS idx_via_id ON Via_Layers (Via_ID);",
        "CREATE INDEX IF NOT EXISTS idx_routing_name ON Routing_Layers (Name);",
        "CREATE INDEX IF NOT EXISTS idx_cut_name ON Cut_Layers (Name);",
        "CREATE INDEX IF NOT EXISTS idx_via_name ON Vias (Name);",
        "CREATE INDEX IF NOT EXISTS idx_via_layer_name ON Via_Layers (Layer_Name);"
    ]

    for query in index_queries:
        cursor.execute(query)

    conn.commit()


def drop_cell_library_corner_columns(conn):
    conn.execute("""
        CREATE TABLE Routing_Layers_New AS
        SELECT Layer_ID, Name, Type, Direction, Pitch_X, Pitch_Y, Offset_X, Offset_Y, Width, Spacing, Area, Thickness, Min_Enclosed_Area, Edge_Capacitance, Capacitance_Per_SQ_Dist, Resistance_Per_SQ, DC_Current_Density_Avg, AC_Current_Density_Rms, Maximum_Density, Density_Check_Window_X, Density_Check_Window_Y, Density_Check_Step, Antenna_Model
        FROM Routing_Layers;
    """)
    conn.execute("DROP TABLE Routing_Layers;")
    conn.execute("ALTER TABLE Routing_Layers_New RENAME TO Routing_Layers;")
    conn.execute("""
        CREATE TABLE Cut_Layers_New AS
        SELECT Layer_ID, Name, Type, Width, Spacing, Enclosure_Below_X, Enclosure_Below_Y, Enclosure_Above_X, Enclosure_Above_Y, Resistance, DC_Current_Density
        FROM Cut_Layers;
    """)
    conn.execute("DROP TABLE Cut_Layers;")
    conn.execute("ALTER TABLE Cut_Layers_New RENAME TO Cut_Layers;")
    conn.execute("""
        CREATE TABLE Vias_New AS
        SELECT Via_ID, Name, Upper_Layer, Lower_Layer
        FROM Vias;
    """)
    conn.execute("DROP TABLE Vias;")
    conn.execute("ALTER TABLE Vias_New RENAME TO Vias;")

    conn.commit() 



def get_tlef_table_names():
    table_names = [
        "Routing_Layers",
        "Antenna_Diff_Side_Area_Ratios",
        "Cut_Layers",
        "Antenna_Diff_Area_Ratios",
        "Vias",
        "Via_Layers"
    ]
    
    return table_names


def save_in_memory_db_to_disk(in_memory_conn, disk_db_path):
    with sqlite3.connect(disk_db_path) as disk_conn:
        in_memory_conn.backup(disk_conn)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_name', type=str, help='Name of the PDK', default="sky130")
    parser.add_argument('--pdk_path', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--partition', help='Partition the database by standard cells and operating conditions.', action='store_true', default=False)
    parser.add_argument('--output_dir', type=str, help='Path to output director', default='./dbs/')
    args = parser.parse_args()

  
    pdk_name = args.pdk_name
    partition = args.partition 
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    db_path = os.path.join(output_dir, f'{pdk_name}_tlef.db')
    delete_database(db_path)
    conn = sqlite3.connect(db_path)
    
    create_tlef_tables(conn)
    
    scl_variants = get_scl(pdk_name=pdk_name)

    techlef_corners = get_techlef_corners(pdk_name=pdk_name)
    
    db_conn = dict()

    if not partition:
        conn = sqlite3.connect(":memory:")  # Single in-memory database
        db_conn["single"] = conn
        create_tlef_tables(conn)  # Create tables once for the single database

    for variant in scl_variants:
        for corner in techlef_corners:
            if partition:
                conn = sqlite3.connect(":memory:")  
                db_conn[f"{variant.value}_tlef_{corner.value}"] = conn
                create_tlef_tables(conn)

    for variant in tqdm.tqdm(scl_variants):
        for corner in tqdm.tqdm(techlef_corners):
            techlef_path =get_techlef_paths(pdk_name, variant.value, corner.value)

            tlef_parser = LefParser(techlef_path)
            tlef_parser.parse()
            print(tlef_parser)
            print(tlef_parser.layer_dict)
            if partition:
                insert_tlef_data(db_conn[f"{variant.value}_{corner.value}"], tlef_parser.layer_dict, tlef_parser.via_dict, corner=corner.value, scl_variant=variant.value)
                drop_cell_library_corner_columns(db_conn[f"{variant.value}_{corner.value}"])
            else:
                insert_tlef_data(db_conn["single"], tlef_parser.layer_dict, tlef_parser.via_dict, corner=corner.value, scl_variant=variant.value)

    if partition:
        for key, conn in db_conn.items():
            parts = key.split('_')
            variant_name = '_'.join(parts[:4])
            corner = parts[4]
            disk_db_path = os.path.join(output_dir, f'{pdk_name}_tlef_{variant_name}_{corner}.db')
            save_in_memory_db_to_disk(conn, disk_db_path)
    else:
        disk_db_path = os.path.join(output_dir, f'{pdk_name}_tlef.db')
        save_in_memory_db_to_disk(db_conn["single"], disk_db_path)

    for conn in db_conn.values():
        conn.close()


if __name__ == '__main__':
    main()