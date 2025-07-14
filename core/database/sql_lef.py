""""Convert Lef file to SQL database
"""

import os 
import re
import sys
import tqdm
import sqlite3
import argparse

from config.pdks import get_scl, get_lef_paths
from core.parsers.lef.lef_parser import LefParser
from core.database.db_utils import delete_database


def insert_lef_data(conn, macros, scl_variant):
    
    cursor = conn.cursor()
    
    for _, macro in macros.items():
        # Insert macro details
        macro.info['SYMMETRY'].remove(';')
        symmetry = ', '.join( macro.info['SYMMETRY'])
    
        cursor.execute('''
        INSERT INTO Macros (Name, Class, Foreign_Name, Origin_X, Origin_Y, Size_Width, Size_Height, Symmetry, Site, Cell_Library)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            macro.name, 
            macro.info['CLASS'], 
            macro.info['FOREIGN'][0],  
            float(macro.info['ORIGIN'][0]),  
            float(macro.info['ORIGIN'][1]),  
            float(macro.info['SIZE'][0]), 
            float(macro.info['SIZE'][1]),  
            symmetry, 
            macro.info['SITE'],
            scl_variant
        ))
                
        macro_id = cursor.lastrowid  # Retrieve the ID of the inserted macro

        # Insert Macro obstruction
        if 'OBS' in macro.info.keys():
            for obs_layer in macro.info['OBS'].info['LAYER']:      
                cursor.execute('''
                INSERT INTO Obstructions (Macro_ID, Layer)
                VALUES (?, ?)
                ''', (
                    macro_id, 
                    obs_layer.name, 
                ))
                
                obs_layer_id = cursor.lastrowid
                
                for rect in obs_layer.shapes:
                    cursor.execute('''
                    INSERT INTO Obstruction_Rectangles (Obstruction_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        obs_layer_id, 
                        float(rect.points[0][0]),  
                        float(rect.points[0][1]),
                        float(rect.points[1][0]),
                        float(rect.points[1][1])                
                    ))
            
        # Insert pin details
        for pin_name, pin in macro.pin_dict.items():
            cursor.execute('''
                INSERT INTO Pins (Macro_ID, Name, Direction, Use, Antenna_Gate_Area, Antenna_Diff_Area)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                macro_id,
                pin_name,  
                pin.info['DIRECTION'], 
                pin.info['USE'] if 'USE' in pin.info.keys() else None,  
                float(pin.info.get('ANTENNAGATEAREA', None)) if pin.info.get('ANTENNAGATEAREA') is not None else None ,  
                float(pin.info.get('ANTENNADIFFAREA', None)) if pin.info.get('ANTENNADIFFAREA') is not None else None 
            ))
           
            pin_id = cursor.lastrowid  # Retrieve the ID of the inserted pin
            
            # Insert port details
            port = pin.info['PORT']
            for layer in port.info['LAYER']: 
                cursor.execute('''
                    INSERT INTO Pin_Ports (Pin_ID, Layer)
                    VALUES (?, ?)
                ''', (
                    pin_id,   
                    layer.name  
                ))
                
                port_id = cursor.lastrowid  # Retrieve the ID of the inserted port

                # Insert rectangle details for each port
                for rect in layer.shapes:
                    cursor.execute('''
                        INSERT INTO Pin_Port_Rectangles (Port_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        port_id, 
                        float(rect.points[0][0]),  
                        float(rect.points[0][1]),
                        float(rect.points[1][0]),
                        float(rect.points[1][1])
                    ))
                                    
        macro_id = cursor.lastrowid  # Retrieve the ID of the inserted macro
        conn.commit()


def get_lef_description(selected_schema=None, partition=False):
    """Returns the description of the tables in the selected schema
    """
    macros_table = """
# Table: Macros
Specifies cells in the library and their physical attributes.
[
    (Macro_ID, the unique identifier of the cell. Value examples: [101, 102, 103, 104]),
    (Name, the name of the cell. Value examples: [sky130_fd_sc_hd__and2_1, sky130_fd_sc_hd__or2_2, sky130_fd_sc_hd__inv_1]),
    (Class, the classification of the cell. Value examples: [CORE, IO, CORNER]),
    (Foreign_Name, the alternative name of the cell used in other contexts. Value examples: [sky130_fd_sc_hd__inv_1, sky130_fd_sc_hd__or2_2, sky130_fd_sc_hd__and2_1]),
    (Origin_X, the x-coordinate of the origin point of the cell within the layout. Value examples: [0.0]),
    (Origin_Y, the y-coordinate of the origin point of the cell within the layout. Value examples: [0.0]),
    (Size_Width, the width of the cell. Value examples: [1.45, 2.35, 0.75]),
    (Size_Height, the height of the cell. Value examples: [2.720]),
    (Symmetry, the symmetry properties of the cell. Value examples: [R90]),
    (Site, the site or standard cell layout used by the cell. Value examples: [unithd])
"""

    if partition:
        macros_table += """
]
"""
    else:
        macros_table += """
    (Cell_Library, standard cell library variant. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls])
]
"""
    pins_table = """
# Table: Pins
Details about pins associated with each macro.
[
    (Pin_ID, the unique identifier for the pin. Value examples: [501, 502, 503]),
    (Macro_ID, the identifier of the macro to which the pin belongs. Value examples: [101, 102, 103]),
    (Name, the name of the pin. Value examples: [A1, A2, B1]),
    (Direction, the direction of the pin, indicating whether it's an input pin (INPUT), output pin (OUTPUT), or bidirectional pin (INOUT). Value examples: [INPUT, OUTPUT, INOUT]),
    (Use, the intended use of the pin, such as signal or power. Value examples: [SIGNAL, POWER, GROUND]),
    (Antenna_Gate_Area, the gate area of the input pin for calculating antenna effects, available only for input pins. Value examples: [0.495, 0.230, 0.150]),
    (Antenna_Diff_Area, the diffusion area of the output pin for calculating antenna effects, available only for output pins. Value examples: [0.245, 0.335, 0.120])
]
"""
    
    ports_table = """
# Table: Pin_Ports
Information about the layers on which macro pins are drawn.
[
    (Port_ID, the unique identifier for each layer entry. Value examples: [1501, 1502, 1503]),
    (Pin_ID, the identifier of the pin to which the layer information is related. Value examples: [501, 502, 503]),
    (Layer, the specific layer of the technology used for the pin, such as metal or polysilicon. Value examples: [met1, met2, pwell, nwell])
]
"""
    
    rect_table = """
# Table: Pin_Port_Rectangles
Contains coordinates for each port rectangle.
[
    (Rect_ID, the unique identifier for each rectangle entry. Value examples: [2501, 2502, 2503]),
    (Port_ID, the identifier of the port to which the rectangle is associated. Value examples: [1501, 1502, 1503]),
    (Rect_X1, the x-coordinate of the lower-left corner of the rectangle. Value examples: [4.245, 5.220, 4.025]),
    (Rect_Y1, the y-coordinate of the lower-left corner of the rectangle. Value examples: [1.595, 1.055, 1.010]),
    (Rect_X2, the x-coordinate of the upper-right corner of the rectangle. Value examples: [5.390, 5.700, 4.420]),
    (Rect_Y2, the y-coordinate of the upper-right corner of the rectangle. Value examples: [1.765, 1.290, 1.275])
]
"""
    
    obs_table = """
# Table: Obstructions
Contains the obstruction layers for each macro.
[
    (Obstruction_ID, the unique identifier for each layer entry associated with a macro. Value examples: [3501, 3502, 3503]),
    (Macro_ID, the identifier of the macro to which the layer information pertains. Value examples: [101, 102, 103]),
    (Layer, the specific layer of the technology stack used in the macro, such as metal or polysilicon. Value examples: [met1, met1])
]
"""
    
    obs_rect_table = """
# Table: Obstruction_Rectangles
Coordinates for each obstruction rectangle.
[
    (Rect_ID, the unique identifier for each rectangle entry. Value examples: [2501, 2502, 2503]),
    (Obstruction_ID, the identifier of the obstruction to which the rectangle is associated. Value examples: [1501, 1502, 1503]),
    (Rect_X1, the x-coordinate of the lower-left corner of the rectangle. Value examples: [4.245, 5.220, 4.025]),
    (Rect_Y1, the y-coordinate of the lower-left corner of the rectangle. Value examples: [1.595, 1.055, 1.010]),
    (Rect_X2, the x-coordinate of the upper-right corner of the rectangle. Value examples: [5.390, 5.700, 4.420]),
    (Rect_Y2, the y-coordinate of the upper-right corner of the rectangle. Value examples: [1.765, 1.290, 1.275])
]
"""
    
    desc = """The LEF file database has the following tables: \n"""

    if selected_schema: 
        if 'Macros' in selected_schema:
            desc += macros_table
            
        if 'Pins' in selected_schema:
            desc += pins_table
        
        if 'Pin_Ports' in selected_schema:
            desc += ports_table
        
        if 'Pin_Port_Rectangles' in selected_schema:
            desc += rect_table
        
        if 'Obstructions' in selected_schema:
            desc += obs_table
            
        if 'Obstruction_Rectangles' in selected_schema:
            desc += obs_rect_table
   
    else:
        desc  = macros_table + pins_table + ports_table + rect_table + obs_table + obs_rect_table
         
    return desc 


def get_compact_lef_description(selected_schema=None):
    """Returns a compact description of the tables in the selected schema"""
    
    macros_table = """
## Macros
Specifies cells and their physical attributes.
- Columns: Macro_ID, Name, Class, Foreign_Name, Origin_X, Origin_Y, Size_Width, Size_Height, Symmetry, Site, Cell_Library
"""

    pins_table = """
## Pins
Details about pins associated with each macro.
- Columns: Pin_ID, Macro_ID, Name, Direction, Use, Antenna_Gate_Area, Antenna_Diff_Area
"""
    
    ports_table = """
## Pin_Ports
Information about layers on which macro pins are drawn.
- Columns: Port_ID, Pin_ID, Layer
"""
    
    rect_table = """
## Pin_Port_Rectangles
Coordinates for each port rectangle.
- Columns: Rect_ID, Port_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2
"""
    
    obs_table = """
## Obstructions
Obstruction layers for each macro.
- Columns: Obstruction_ID, Macro_ID, Layer
"""
    
    obs_rect_table = """
## Obstruction_Rectangles
Coordinates for each obstruction rectangle.
- Columns: Rect_ID, Obstruction_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2
"""
    
    desc = "# LEF Database Tables\n"

    if selected_schema: 
        if 'Macros' in selected_schema:
            desc += macros_table
        if 'Pins' in selected_schema:
            desc += pins_table
        if 'Pin_Ports' in selected_schema:
            desc += ports_table
        if 'Pin_Port_Rectangles' in selected_schema:
            desc += rect_table
        if 'Obstructions' in selected_schema:
            desc += obs_table
        if 'Obstruction_Rectangles' in selected_schema:
            desc += obs_rect_table
    else:
        desc += macros_table + pins_table + ports_table + rect_table + obs_table + obs_rect_table
         
    return desc.strip()


def create_lef_tables(conn):
    
    cursor = conn.cursor()
    
    # Create the 'macros' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Macros (
        Macro_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT UNIQUE NOT NULL,
        Class TEXT,
        Foreign_Name TEXT,
        Origin_X REAL,
        Origin_Y REAL,
        Size_Width REAL,
        Size_Height REAL,
        Symmetry TEXT,
        Site TEXT,
        Cell_Library TEXT 
    );
    ''')

    # Create the 'pins' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Pins (
        Pin_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Macro_ID INTEGER NOT NULL,
        Name TEXT,
        Direction TEXT,
        Use TEXT,
        Antenna_Gate_Area REAL,
        Antenna_Diff_Area REAL,
        FOREIGN KEY (Macro_ID) REFERENCES Macros(Macro_ID)
    );
    ''')

    # Create the 'ports' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Pin_Ports (
        Port_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Pin_ID INTEGER NOT NULL,
        Layer TEXT,
        FOREIGN KEY (Pin_ID) REFERENCES Pins(Pin_ID)
    );
    ''')

    # Create the 'rectangles' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Pin_Port_Rectangles (
        Rect_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Port_ID INTEGER NOT NULL,
        Rect_X1 REAL,
        Rect_Y1 REAL,
        Rect_X2 REAL,
        Rect_Y2 REAL,
        FOREIGN KEY (Port_ID) REFERENCES Pin_Ports(Port_ID)
    );
    ''')

    # Create the 'obs' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Obstructions (
        Obstruction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Macro_ID INTEGER NOT NULL,
        Layer TEXT,
        FOREIGN KEY (Macro_ID) REFERENCES Macros(Macro_ID)
    );
    ''')

    # Create the 'obs_rectangles' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Obstruction_Rectangles (
        Obstruction_Rect_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Obstruction_ID INTEGER NOT NULL,
        Rect_X1 REAL,
        Rect_Y1 REAL,
        Rect_X2 REAL,
        Rect_Y2 REAL,
        FOREIGN KEY (Obstruction_ID) REFERENCES Obstructions(Obstruction_ID)
    );
    ''')
    
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_macro_id ON Macros (Macro_ID);",
        "CREATE INDEX IF NOT EXISTS idx_macro_name ON Macros (Name);",
        "CREATE INDEX IF NOT EXISTS idx_pin_id ON Pins (Pin_ID);",
        "CREATE INDEX IF NOT EXISTS idx_pin_name ON Pins (Name);",
        "CREATE INDEX IF NOT EXISTS idx_port_id ON Pin_Ports (Port_ID);",
        "CREATE INDEX IF NOT EXISTS idx_port_rect_id ON Pin_Port_Rectangles (Rect_ID);",
        "CREATE INDEX IF NOT EXISTS idx_obs_id ON Obstructions (Obstruction_ID);",
        "CREATE INDEX IF NOT EXISTS idx_obs_rect_id ON Obstruction_Rectangles (Obstruction_Rect_ID);",
    ]

    for query in index_queries:
        cursor.execute(query)

    conn.commit()



def drop_cell_library_column(conn):
    conn.execute("""
        CREATE TABLE Macros_New AS
        SELECT Macro_ID, Name, Class, Foreign_Name, Origin_X, Origin_Y, Size_Width, Size_Height, Symmetry, Site
        FROM Macros;
    """)
    conn.execute("DROP TABLE Macros;")
    conn.execute("ALTER TABLE Macros_New RENAME TO Macros;")
    conn.commit()
 


def get_lef_table_names():
    table_names =  [
        "Macros",
        "Pins",
        "Pin_Ports",
        "Pin_Port_Rectangles",
        "Obstructions",
        "Obstruction_Rectangles"
    ]

    return table_names 


def get_lef_foreign_keys(selected_schema):
    fk_str = ""
    if selected_schema != None: 
        macro_pins = 'Macros.`Macro_ID` = Pins.`Macro_ID` \n'
        macro_obs = 'Macros.`Macro_ID` = Obstructions.`Macro_ID` \n'
        pins_pinports = 'Pins.`Pin_ID` = Pin_Ports.`Pin_ID` \n'
        pinport_rect = 'Pin_Ports.`Port_ID` = Pin_Port_Rectangles.`Port_ID` \n'
        obs_rect = 'Obstructions.`Obstruction_ID` = Obstruction_Rectangles.`Obstruction_ID` \n'
        
        if set(['Macros', 'Pins']).issubset(set(selected_schema)):
            fk_str+=macro_pins

        if set(['Macros', 'Obstructions']).issubset(set(selected_schema)):
            fk_str+=macro_obs

        if set(['Pins', 'Pin_Ports']).issubset(set(selected_schema)):
            fk_str+=pins_pinports
        
        if set(['Pin_Ports', 'Pin_Port_Rectangles']).issubset(set(selected_schema)):
            fk_str+=pinport_rect

        if set(['Obstructions', 'Obstruction_Rectangles']).issubset(set(selected_schema)):
            fk_str+=obs_rect
            
    else: 
        fk_str = """
Macros.Macro_ID = Pins.Macro_ID 
Pins.Pin_ID = Pin_Ports.Pin_ID 
Pin_Ports.Port_ID = Pin_Port_Rectangles.Port_ID
Macros.Macro_ID = Obstructions.Macro_ID
Obstructions.Obstruction_ID = Obstruction_Rectangles.Obstruction_ID
"""
    return fk_str 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_name', type=str, help='Name of the PDK', default="sky130")
    parser.add_argument('--partition', help='Partition the database by standard cells and operating conditions.', action='store_true', default=False)
    parser.add_argument('--output_dir', type=str, help='Path to output director', default='./dbs/')
    args = parser.parse_args()
    
    pdk_name = args.pdk_name
    partition = args.partition
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    scl_variants = get_scl(pdk_name)
 
    db_path = os.path.join(output_dir, f'{pdk_name}_lef.db')
    delete_database(db_path)
    conn = sqlite3.connect(db_path)

    db_conn = dict()

    if not partition:
        conn = sqlite3.connect(":memory:")
        db_conn["single"] = conn
        create_lef_tables(conn) 

    for variant in scl_variants:
        if partition:
            conn = sqlite3.connect(":memory:")
            db_conn[variant.value] = conn
            create_lef_tables(conn)

    for variant in tqdm.tqdm(scl_variants):
        lef_paths = get_lef_paths(pdk_name, variant.value)
       
        for path in lef_paths: 
            print(path)
            lef_parser = LefParser(path)
            lef_parser.parse()

            if partition:
                insert_lef_data(db_conn[variant.value], lef_parser.macro_dict, scl_variant=variant.value)
                drop_cell_library_column(db_conn[variant.value])
            else:
                insert_lef_data(db_conn["single"], lef_parser.macro_dict, scl_variant=variant.value)


    if partition:
        for variant_name, conn in db_conn.items():
            disk_db_path = os.path.join(output_dir, f'{pdk_name}_lef_{variant_name}.db')
            with sqlite3.connect(disk_db_path) as disk_conn:
                conn.backup(disk_conn)
    else:
        disk_db_path = os.path.join(output_dir, f'{pdk_name}_lef.db')
        with sqlite3.connect(disk_db_path) as disk_conn:
            db_conn["single"].backup(disk_conn)

    for conn in db_conn.values():
        conn.commit()
        conn.close()



if __name__ == '__main__':
    main()