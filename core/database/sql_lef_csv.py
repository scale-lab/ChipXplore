import os
import csv
import sqlite3
import argparse
from enum import Enum
from tqdm import tqdm

from core.parsers.lef.lef_parser import LefParser
from core.database.sql_lef import create_lef_tables
from core.database.db_utils import delete_database, import_csv_to_sql, write_to_csv, write_to_csv_header


class LEFTables(Enum):
    Macros = "Macros" 
    Pins = "Pins" 
    Pin_Ports = "Pin_Ports"
    Pin_Port_Rectangles = "Pin_Port_Rectangles"
    Obstructions = "Obstructions"
    Obstruction_Rectangles = "Obstruction_Rectangles"


def validate_foreign_keys(conn):
    cursor = conn.cursor()
    queries = [
        "SELECT COUNT(*) FROM Pins WHERE Macro_ID NOT IN (SELECT Macro_ID FROM Macros);",
        "SELECT COUNT(*) FROM Pin_Ports WHERE Pin_ID NOT IN (SELECT Pin_ID FROM Pins);",
        "SELECT COUNT(*) FROM Pin_Port_Rectangles WHERE Port_ID NOT IN (SELECT Port_ID FROM Pin_Ports);",
        "SELECT COUNT(*) FROM Obstruction_Rectangles WHERE Obstruction_ID NOT IN (SELECT Obstruction_ID FROM Obstructions);"
    ]
    for query in queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Validation error: {count} invalid foreign key entries.")
        else:
            print("Validation passed for query:", query)


def generate_lef_csv_files(ids, macros, scl_variant, output_dir):
    """Generate CSV files from LEF data."""
    os.makedirs(output_dir, exist_ok=True)

    macro_rows = []
    pin_rows = []
    port_rows = []
    rect_rows = []
    obs_rows = []
    obs_rect_rows = []

    macro_id = ids['Macros']
    pin_id_counter = ids['Pins']
    port_id_counter = ids['Pin_Ports']
    port_rect_id_counter = ids['Pin_Port_Rectangles']
    obs_id_counter = ids['Obstructions']
    obs_rect_id_counter = ids['Obstruction_Rectangles']

    for _, (macro_name, macro) in enumerate(macros.items(), start=1):

        macro.info['SYMMETRY'].remove(';')
        symmetry = ', '.join(macro.info['SYMMETRY'])
        macro_rows.append([
            macro_id,
            macro.name, 
            macro.info['CLASS'], 
            macro.info['FOREIGN'][0],
            float(macro.info['ORIGIN'][0]), float(macro.info['ORIGIN'][1]),
            float(macro.info['SIZE'][0]), float(macro.info['SIZE'][1]),
            symmetry, 
            macro.info['SITE'], 
            scl_variant
        ])

        # Obstructions
        for obs_layer in macro.info['OBS'].info['LAYER']:
            obs_rows.append([obs_id_counter, macro_id, obs_layer.name])
            for rect in obs_layer.shapes:
                obs_rect_rows.append([
                    obs_rect_id_counter, 
                    obs_id_counter,
                    float(rect.points[0][0]), float(rect.points[0][1]),
                    float(rect.points[1][0]), float(rect.points[1][1])
                ])

                obs_rect_id_counter += 1 
            
            obs_id_counter += 1 

        # Pins
        for pin_name, pin in macro.pin_dict.items():
            pin_rows.append([
                pin_id_counter,
                macro_id, 
                pin_name, 
                pin.info['DIRECTION'],
                pin.info.get('USE'),
                float(pin.info.get('ANTENNAGATEAREA', None)) if pin.info.get('ANTENNAGATEAREA') is not None else None ,  
                float(pin.info.get('ANTENNADIFFAREA', None)) if pin.info.get('ANTENNADIFFAREA') is not None else None 
            ])

            # Ports
            port = pin.info['PORT']
            for layer in port.info['LAYER']:
                port_rows.append([port_id_counter, pin_id_counter, layer.name])
                for rect in layer.shapes:
                    rect_rows.append([
                        port_rect_id_counter,
                        port_id_counter, 
                        float(rect.points[0][0]), float(rect.points[0][1]),
                        float(rect.points[1][0]), float(rect.points[1][1])
                    ])

                    port_rect_id_counter += 1
                port_id_counter += 1
            
            pin_id_counter += 1

        macro_id += 1 

    # Write to CSV files
    write_to_csv(os.path.join(output_dir, 'Macros.csv'), macro_rows)
    write_to_csv(os.path.join(output_dir, 'Pins.csv'), pin_rows)
    write_to_csv(os.path.join(output_dir, 'Pin_Ports.csv'), port_rows)
    write_to_csv(os.path.join(output_dir, 'Pin_Port_Rectangles.csv'), rect_rows)
    write_to_csv(os.path.join(output_dir, 'Obstructions.csv'), obs_rows)
    write_to_csv(os.path.join(output_dir, 'Obstruction_Rectangles.csv'), obs_rect_rows)

    ids['Macros'] = macro_id
    ids['Pins'] = pin_id_counter
    ids['Pin_Ports'] = port_id_counter
    ids['Pin_Port_Rectangles'] = port_rect_id_counter
    ids['Obstructions'] = obs_id_counter
    ids['Obstruction_Rectangles'] = obs_rect_id_counter

    return ids 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_path', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--output_dir', type=str, help='Path to output directory', default='./dbs/')
    args = parser.parse_args()

    pdk_root = os.environ.get('PDK_ROOT')
    pdk_path = os.path.join(pdk_root, 'sky130A', 'libs.ref') if pdk_root else  args.pdk_path

    output_dir = args.output_dir
    
    os.makedirs(output_dir, exist_ok=True)

    db_path = os.path.join(output_dir, 'sky_lef_csv.db')

    delete_database(db_path)

    scl_variants = [
        "sky130_fd_sc_hdll",
        "sky130_fd_sc_ls",
        "sky130_fd_sc_hs",
        "sky130_fd_sc_lp",
        "sky130_fd_sc_ms",
        "sky130_fd_sc_hd",
    ]
        
    write_to_csv_header(os.path.join(output_dir, 'Macros.csv'),
        ['Macro_ID', 'Name', 'Class', 'Foreign_Name', 'Origin_X', 'Origin_Y', 'Size_Width', 'Size_Height', 'Symmetry', 'Site', 'Cell_Library'])

    write_to_csv_header(os.path.join(output_dir, 'Pins.csv'),
        ['Pin_ID', 'Macro_ID', 'Name', 'Direction', 'Use', 'Antenna_Gate_Area', 'Antenna_Diff_Area'])

    write_to_csv_header(os.path.join(output_dir, 'Pin_Ports.csv'),
        ['Port_ID', 'Pin_ID', 'Layer'])

    write_to_csv_header(os.path.join(output_dir, 'Pin_Port_Rectangles.csv'),
        ['Rect_ID', 'Port_ID', 'Rect_X1', 'Rect_Y1', 'Rect_X2', 'Rect_Y2'])

    write_to_csv_header(os.path.join(output_dir, 'Obstructions.csv'),
        ['Obstruction_ID', 'Macro_ID', 'Layer'])

    write_to_csv_header(os.path.join(output_dir, 'Obstruction_Rectangles.csv'), 
        ['Obstruction_Rect_ID', 'Obstruction_ID', 'Rect_X1', 'Rect_Y1', 'Rect_X2', 'Rect_Y2'])
    
    ids = {
        'Macros': 1,
        'Pins': 1,
        'Pin_Ports': 1,
        'Pin_Port_Rectangles': 1,
        'Obstructions': 1,
        'Obstruction_Rectangles': 1
    }
    for variant in tqdm(scl_variants):
        lef_path = os.path.join(pdk_path, variant, 'lef', f"{variant}.lef")
        lef_parser = LefParser(lef_path)
        lef_parser.parse()
       
        ids = generate_lef_csv_files(ids, lef_parser.macro_dict, variant, output_dir)

    conn = sqlite3.connect(db_path)
    create_lef_tables(conn)

    for table, file_name, columns in [
        ("Macros", "Macros.csv", "Macro_ID, Name, Class, Foreign_Name, Origin_X, Origin_Y, Size_Width, Size_Height, Symmetry, Site, Cell_Library"),
        ("Pins", "Pins.csv", "Pin_ID, Macro_ID, Name, Direction, Use, Antenna_Gate_Area, Antenna_Diff_Area"),
        ("Pin_Ports", "Pin_Ports.csv", "Port_ID, Pin_ID, Layer"),
        ("Pin_Port_Rectangles", "Pin_Port_Rectangles.csv", "Rect_ID, Port_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2"),
        ("Obstructions", "Obstructions.csv", "Obstruction_ID, Macro_ID, Layer"),
        ("Obstruction_Rectangles", "Obstruction_Rectangles.csv", "Obstruction_Rect_ID, Obstruction_ID, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2")
    ]:
        import_csv_to_sql(conn, os.path.join(output_dir, file_name), table, columns)

    
    validate_foreign_keys(conn)

    conn.close()

if __name__ == '__main__':
    main()
