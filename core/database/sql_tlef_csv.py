import os
import csv
import sqlite3
import argparse
from tqdm import tqdm

from core.parsers.lef.lef_parser import LefParser
from core.database.db_utils import delete_database, import_csv_to_sql, write_to_csv, write_to_csv_header
from core.database.sql_tlef import create_tlef_tables, parse_via_name


def generate_tlef_csv_files(ids, layer_dict, via_dict, corner, scl_variant, output_dir):
    """Generate CSV files from TLEF data."""
    os.makedirs(output_dir, exist_ok=True)

    routing_layer_rows = []
    cut_layer_rows = []
    antenna_diff_side_area_rows = []
    antenna_diff_area_rows = []
    via_rows = []
    via_layer_rows = []

    routing_layer_id = ids['Routing_Layers']
    cut_layer_id = ids['Cut_Layers']
    diff_side_area_ratio_id = ids['Antenna_Diff_Side_Area_Ratios']
    diff_area_ratio_id = ids['Antenna_Diff_Area_Ratios']
    via_id = ids['Vias']
    via_layer_id = ids['Via_Layers']

    # Routing Layers
    for _, (layer_name, layer) in enumerate(layer_dict.items(), start=1):
        if layer.layer_type == "ROUTING":
                
            if layer.pitch: 
                pitch_x = float(layer.pitch[0]) if isinstance(layer.pitch, tuple) else float(layer.pitch)
                pitch_y = float(layer.pitch[0]) if isinstance(layer.pitch, tuple) else float(layer.pitch)
            else:
                pitch_x = None 
                pitch_y = None 

            if layer.offset: 
                offset_x = float(layer.offset[0]) if isinstance(layer.offset, tuple) else float(layer.offset)
                offset_y = float(layer.offset[1]) if isinstance(layer.offset, tuple) else float(layer.offset)
            else:
                offset_x = None 
                offset_y = None 
            
            routing_layer_rows.append([
                routing_layer_id, 
                layer.name, 
                layer.layer_type, 
                layer.direction,
                pitch_x,
                pitch_y,
                offset_x,
                offset_y,
                layer.width, 
                layer.spacing, 
                layer.area, 
                layer.thickness,
                layer.min_enclosed_area, 
                layer.edge_cap,
                layer.capacitance[1] if layer.capacitance else None,
                layer.resistance if isinstance(layer.resistance, float) else layer.resistance[1],
                layer.dc_current_density[1] if layer.dc_current_density else None,
                layer.ac_current_density[1] if layer.ac_current_density else None,
                layer.max_density, 
                layer.density_check_window[0] if layer.density_check_window else None,
                layer.density_check_window[1] if layer.density_check_window else None,
                layer.density_check_step, 
                layer.antenna_model, 
                corner, 
                scl_variant
            ])

            if layer.antenna_diff_side_area_ratio:
                antenna_diff_side_area = layer.antenna_diff_side_area_ratio
                antenna_diff_side_area_rows.append([
                    diff_side_area_ratio_id,
                    routing_layer_id, 
                    antenna_diff_side_area[0],
                    antenna_diff_side_area[1][0], antenna_diff_side_area[1][1], 
                    antenna_diff_side_area[2][0], antenna_diff_side_area[2][1], 
                    antenna_diff_side_area[3][0], antenna_diff_side_area[3][1],
                    antenna_diff_side_area[4][0], antenna_diff_side_area[4][1]
                ])

                diff_side_area_ratio_id += 1

            routing_layer_id += 1

        elif layer.layer_type == "CUT":

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

            cut_layer_rows.append([
                cut_layer_id,
                layer.name, 
                layer.layer_type, 
                layer.width, 
                layer.spacing,
                enclosure_below_x, 
                enclosure_below_y, 
                enclosure_above_x, 
                enclosure_above_y,
                layer.resistance,
                layer.dc_current_density[1] if layer.dc_current_density else None,
                corner, 
                scl_variant
            ])
            if layer.antenna_diff_area_ratio:
                antenna_diff_area = layer.antenna_diff_area_ratio
                antenna_diff_area_rows.append([
                    diff_area_ratio_id,
                    cut_layer_id, 
                    antenna_diff_area[0],
                    antenna_diff_area[1][0], antenna_diff_area[1][1], 
                    antenna_diff_area[2][0], antenna_diff_area[2][1], 
                    antenna_diff_area[3][0], antenna_diff_area[3][1],
                    antenna_diff_area[4][0], antenna_diff_area[4][1]
                ])

                diff_area_ratio_id += 1

            cut_layer_id += 1
  
    # Vias
    for _, via in enumerate(via_dict.values(), start=1):
        metal_layers = parse_via_name(via.name)
  
        via_rows.append([
            via_id, 
            via.name, 
            metal_layers['lower_layer'],
            metal_layers['upper_layer'], 
            corner,
            scl_variant
        ])

        for layer in via.layers:
            via_layer_rows.append([
                via_layer_id, 
                via_id,
                layer.name,
                layer.shapes[0].points[0][0], layer.shapes[0].points[0][1],
                layer.shapes[0].points[1][0], layer.shapes[0].points[1][1]
            ])
            via_layer_id += 1

        via_id += 1

    # Write to CSV files
    write_to_csv(os.path.join(output_dir, 'Routing_Layers.csv'), routing_layer_rows)
    write_to_csv(os.path.join(output_dir, 'Cut_Layers.csv'), cut_layer_rows)
    write_to_csv(os.path.join(output_dir, 'Antenna_Diff_Side_Area_Ratios.csv'), antenna_diff_side_area_rows)
    write_to_csv(os.path.join(output_dir, 'Antenna_Diff_Area_Ratios.csv'), antenna_diff_area_rows)
    write_to_csv(os.path.join(output_dir, 'Vias.csv'), via_rows)
    write_to_csv(os.path.join(output_dir, 'Via_Layers.csv'), via_layer_rows)

    ids = {
        'Routing_Layers': routing_layer_id,
        'Cut_Layers': cut_layer_id,
        'Antenna_Diff_Side_Area_Ratios': diff_side_area_ratio_id,
        'Antenna_Diff_Area_Ratios': diff_area_ratio_id,
        'Vias': via_id,
        'Via_Layers': via_layer_id
    }

    return ids 


def validate_foreign_keys(conn):
    cursor = conn.cursor()
    queries = [
        "SELECT COUNT(*) FROM Antenna_Diff_Side_Area_Ratios WHERE Routing_Layer_ID NOT IN (SELECT Layer_ID FROM Routing_Layers);",
        "SELECT COUNT(*) FROM Antenna_Diff_Area_Ratios WHERE Cut_Layer_ID NOT IN (SELECT Layer_ID FROM Cut_Layers);",
        "SELECT COUNT(*) FROM Via_Layers WHERE Via_ID NOT IN (SELECT Via_ID FROM Vias);"
    ]
    for query in queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Validation error: {count} invalid foreign key entries.")
        else:
            print("Validation passed for query:", query)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_path', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--output_dir', type=str, help='Path to output directory', default='./dbs/')
    args = parser.parse_args()

    # Determine PDK root path
    pdk_root = os.environ.get('PDK_ROOT')
    pdk_path = os.path.join(pdk_root, 'sky130A', 'libs.ref') if pdk_root else args.pdk_path

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    db_path = os.path.join(output_dir, 'sky_tlef_Csv.db')
    delete_database(db_path)

    conn = sqlite3.connect(db_path)

    create_tlef_tables(conn)

    scl_variants = [
        "sky130_fd_sc_hdll",
        "sky130_fd_sc_ls",
        "sky130_fd_sc_hs",
        "sky130_fd_sc_lp",
        "sky130_fd_sc_ms",
        "sky130_fd_sc_hd",
    ]

    techlef_corners = ["min", "max", "nom"]

    # Write to CSV files
    write_to_csv_header(os.path.join(output_dir, 'Routing_Layers.csv'),
        ['Layer_ID', 'Name', 'Type', 'Direction', 'Pitch_X', 'Pitch_Y', 'Offset_X', 'Offset_Y', 'Width',
        'Spacing', 'Area', 'Thickness', 'Min_Enclosed_Area', 'Edge_Capacitance',
        'Capacitance_Per_SQ_Dist', 'Resistance_Per_SQ', 'DC_Current_Density_Avg',
        'AC_Current_Density_Rms', 'Maximum_Density', 'Density_Check_Window_X',
        'Density_Check_Window_Y', 'Density_Check_Step', 'Antenna_Model', 'Corner', 'Cell_Library'])

    write_to_csv_header(os.path.join(output_dir, 'Cut_Layers.csv'),
        ['Layer_ID', 'Name', 'Type', 'Width', 'Spacing', 'Enclosure_Below_X', 'Enclosure_Below_Y',
        'Enclosure_Above_X', 'Enclosure_Above_Y', 'Resistance', 'DC_Current_Density', 'Corner',
        'Cell_Library'])

    write_to_csv_header(os.path.join(output_dir, 'Antenna_Diff_Side_Area_Ratios.csv'),
        ['Ratio_ID', 'Routing_Layer_ID', 'Type', 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4'])

    write_to_csv_header(os.path.join(output_dir, 'Antenna_Diff_Area_Ratios.csv'),
        ['Ratio_ID', 'Cut_Layer_ID', 'Type', 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4'])

    write_to_csv_header(os.path.join(output_dir, 'Vias.csv'),
        ['Via_ID', 'Name', 'Lower_Layer', 'Upper_Layer', 'Corner', 'Cell_Library'])

    write_to_csv_header(os.path.join(output_dir, 'Via_Layers.csv'),
        ['Via_Layer_ID', 'Via_ID', 'Layer_Name', 'Rect_X1', 'Rect_Y1', 'Rect_X2', 'Rect_Y2'])


    ids = {
        'Routing_Layers': 1 ,
        'Cut_Layers': 1,
        'Antenna_Diff_Side_Area_Ratios': 1,
        'Antenna_Diff_Area_Ratios': 1,
        'Vias': 1,
        'Via_Layers': 1
    }

    for variant in tqdm(scl_variants, desc="Processing SCL Variants"):
        for tlef_corner in tqdm(techlef_corners, desc=f"Processing Corners for {variant}"):
            techlef_path = os.path.join(pdk_path, variant, 'techlef', f"{variant}__{tlef_corner}.tlef")
            tlef_parser = LefParser(techlef_path)
            tlef_parser.parse()

            ids = generate_tlef_csv_files(
                ids=ids,
                layer_dict=tlef_parser.layer_dict, 
                via_dict=tlef_parser.via_dict, 
                corner=tlef_corner, 
                scl_variant=variant, 
                output_dir=output_dir
            )

    for table, file_name, columns in [
        ("Routing_Layers", "Routing_Layers.csv", "Layer_ID, Name, Type, Direction, Pitch_X, Pitch_Y, Offset_X, Offset_Y, Width, Spacing, Area, Thickness, Min_Enclosed_Area, Edge_Capacitance, Capacitance_Per_SQ_Dist, Resistance_Per_SQ, DC_Current_Density_Avg, AC_Current_Density_Rms, Maximum_Density, Density_Check_Window_X, Density_Check_Window_Y, Density_Check_Step, Antenna_Model, Corner, Cell_Library"),
        ("Cut_Layers", "Cut_Layers.csv", "Layer_ID, Name, Type, Width, Spacing, Enclosure_Below_X, Enclosure_Below_Y, Enclosure_Above_X, Enclosure_Above_Y, Resistance, DC_Current_Density, Corner, Cell_Library"),
        ("Antenna_Diff_Side_Area_Ratios", "Antenna_Diff_Side_Area_Ratios.csv", "Ratio_ID, Routing_Layer_ID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4"),
        ("Antenna_Diff_Area_Ratios", "Antenna_Diff_Area_Ratios.csv", "Ratio_ID, Cut_Layer_ID, Type, X1, Y1, X2, Y2, X3, Y3, X4, Y4"),
        ("Vias", "Vias.csv", "Via_ID, Name, Lower_Layer, Upper_Layer, Corner, Cell_Library"),
        ("Via_Layers", "Via_Layers.csv", "Via_Layer_ID, Via_ID, Layer_Name, Rect_X1, Rect_Y1, Rect_X2, Rect_Y2")
    ]:
        csv_file_path = os.path.join(output_dir, file_name)
        import_csv_to_sql(conn, csv_file_path, table, columns)

    conn.commit()

    validate_foreign_keys(conn)

    conn.close()


if __name__ == '__main__':
    main()
