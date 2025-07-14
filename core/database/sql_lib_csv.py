import os
import csv
import sqlite3
import argparse
from tqdm import tqdm
from core.parsers.lib.lib_parser import parse_liberty_file
from core.database.db_utils import delete_database, import_csv_to_sql, write_to_csv, write_to_csv_header
from core.database.sql_lib import create_lib_tables



def generate_lib_csv_files(ids, cells, operating_conditions, cell_variant, output_dir):

    op_cond_id = ids['Operating_Conditions'] 
    cell_id = ids['Cells'] 
    input_pin_id = ids['Input_Pins'] 
    output_pin_id = ids['Output_Pins'] 
    timing_value_id = ids['Timing_Values'] 

    operating_conditions_rows = [[
        op_cond_id,
        operating_conditions['name'],
        operating_conditions['voltage'],
        operating_conditions['process'],
        operating_conditions['temperature'],
        operating_conditions['tree_type'],
        cell_variant
    ]]

    cells_rows = []
    input_pins_rows = []
    output_pins_rows = []
    timing_values_rows = []

    for cell in tqdm(cells, desc="Processing cells"):
        cells_rows.append([
            cell_id, 
            cell['name'], 
            cell['drive'], 
            cell['area'], 
            cell['cell_footprint'],
            cell['cell_leakage_power'], 
            cell['driver_waveform_fall'], 
            cell['driver_waveform_rise'],
            cell['is_buffer'], 
            cell['is_inverter'], 
            cell['is_flip_flop'],
            cell['is_scan_enabled_flip_flop'],
            op_cond_id
        ])

        for pin in cell['pins']:
            if pin['direction'] == "input":
                is_clock = True if pin.get('clock', 'false').lower() == "true" else False

                input_pins_rows.append([
                    input_pin_id, 
                    cell_id, 
                    pin['name'],
                    is_clock,
                    pin['capacitance'], 
                    float(pin['fall_capacitance']) if 'fall_capacitance' in pin.keys() else None,
                    float(pin['rise_capacitance'])  if 'rise_capacitance' in pin.keys() else None,
                    float(pin['max_transition']) if 'max_transition' in pin.keys() else None,
                    pin.get('related_power_pin'), 
                    pin.get('related_ground_pin')
                ])
                
            elif pin['direction'] == "output":
                output_pins_rows.append([
                    output_pin_id, 
                    cell_id, 
                    pin['name'], 
                    pin.get('function', None),
                    float(pin['max_capacitance']) if 'max_capacitance' in pin.keys() else None,
                    float(pin['max_transition']) if 'max_transition' in pin.keys() else None,
                    str(pin['power_down_function']) if 'power_down_function' in pin.keys() else None,
                    pin.get('related_power_pin'), 
                    pin.get('related_ground_pin')
                ])
                output_pin_id += 1

            if 'timing' in pin:
                for related_pin, timing_entries in pin['timing'].items():
                    for timing_entry in timing_entries:
                        timing_values_rows.append([
                            timing_value_id, 
                            cell_id, 
                            output_pin_id,
                            related_pin,
                            timing_entry['index_1'], 
                            timing_entry['index_2'],
                            timing_entry['fall_delay'],
                            timing_entry['rise_delay'],
                            timing_entry['average_delay'],
                            timing_entry['fall_transition'],
                            timing_entry['rise_transition']
                        ])
                        timing_value_id += 1

            if pin['direction'] == "input":
                input_pin_id += 1
            elif pin['direction'] == "output":
                output_pin_id += 1

        cell_id += 1

    op_cond_id += 1
    # Write to CSV files
    write_to_csv(os.path.join(output_dir, 'Operating_Conditions.csv'), operating_conditions_rows)
    write_to_csv(os.path.join(output_dir, 'Cells.csv'), cells_rows)
    write_to_csv(os.path.join(output_dir, 'Input_Pins.csv'), input_pins_rows)
    write_to_csv(os.path.join(output_dir, 'Output_Pins.csv'), output_pins_rows)
    write_to_csv(os.path.join(output_dir, 'Timing_Values.csv'), timing_values_rows)

    ids = {
        'Operating_Conditions': op_cond_id,
        'Cells': cell_id,
        'Input_Pins': input_pin_id,
        'Output_Pins': output_pin_id,
        'Timing_Values': timing_value_id
    }

    return ids


def import_csv_to_sql(conn, csv_file, table_name, columns):
    """Import CSV data into a SQL table."""
    cursor = conn.cursor()
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        cursor.executemany(f'INSERT INTO {table_name} ({columns}) VALUES ({", ".join(["?" for _ in columns.split(",")])})', reader)
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_path', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--output_dir', type=str, help='Path to output director', default='./dbs/')
    args = parser.parse_args()
    
    pdk_root = os.environ.get('PDK_ROOT')
    pdk_path = os.path.join(pdk_root, 'sky130A', 'libs.ref') if pdk_root else  args.pdk_path
    
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    database_path =  os.path.join(output_dir, 'sky_lib.db')
    delete_database(database_path)
   
    conn = sqlite3.connect(database_path)

    create_lib_tables(conn, unified_timing_tables=True)

    scl_variants = [
        "sky130_fd_sc_hdll",
        "sky130_fd_sc_ls",
        # "sky130_fd_sc_hs",
        # "sky130_fd_sc_lp",
        # "sky130_fd_sc_ms",
        # "sky130_fd_sc_hd",
    ]

    # Write to CSV files
    write_to_csv_header(os.path.join(output_dir, 'Operating_Conditions.csv'),
        ['Condition_ID', 'Name', 'Voltage', 'Process', 'Temperature', 'Tree_Type', 'Cell_Library'])

    write_to_csv_header(os.path.join(output_dir, 'Cells.csv'),
        ['Cell_ID', 'Name', 'Drive_Strength', 'Area', 'Cell_Footprint', 'Leakage_Power',
        'Driver_Waveform_Fall', 'Driver_Waveform_Rise', 'Is_Buffer', 'Is_Inverter', 'Is_Flip_Flop',
        'Is_Scan_Enabled_Flip_Flop', 'Condition_ID'])

    write_to_csv_header(os.path.join(output_dir, 'Input_Pins.csv'),
        ['Input_Pin_ID', 'Cell_ID', 'Input_Pin_Name', 'Clock', 'Capacitance', 'Fall_Capacitance',
        'Rise_Capacitance', 'Max_Transition', 'Related_Power_Pin', 'Related_Ground_Pin'])

    write_to_csv_header(os.path.join(output_dir, 'Output_Pins.csv'),
        ['Output_Pin_ID', 'Cell_ID', 'Output_Pin_Name', 'Function', 'Max_Capacitance', 'Max_Transition',
        'Power_Down_Function', 'Related_Power_Pin', 'Related_Ground_Pin'])

    write_to_csv_header(os.path.join(output_dir, 'Timing_Values.csv'),
        ['Timing_Value_ID', 'Cell_ID', 'Output_Pin_ID', 'Related_Input_Pin', 'Input_Transition',
        'Output_Capacitance', 'Fall_Delay', 'Rise_Delay', 'Average_Delay', 'Fall_Transition', 'Rise_Transition'])


    ids = {
        'Operating_Conditions': 1,
        'Cells': 1,
        'Input_Pins': 1,
        'Output_Pins': 1,
        'Timing_Values': 1
    }

    for variant in tqdm(scl_variants): 
        lib_path = os.path.join(pdk_path, variant, 'lib')
        for corner in  tqdm(os.listdir(lib_path)):
            if 'ccsnoise' in corner or 'pwrlkg' in corner or 'ka1v76' in corner: # ignore ccsnoise 
                continue

            print("Running Corner: ", corner) 
            corner_path =  os.path.join(lib_path, corner)
            cells, operating_conditions = parse_liberty_file(corner_path)

            ids = generate_lib_csv_files(
                ids,
                cells, 
                operating_conditions, 
                variant,
                output_dir
            )

    for table, file_name, columns in [
        ("Operating_Conditions", "Operating_Conditions.csv", "Condition_ID, Name, Voltage, Process, Temperature, Tree_Type, Cell_Library"),
        ("Cells", "Cells.csv", "Cell_ID, Name, Drive_Strength, Area, Cell_Footprint, Leakage_Power, Driver_Waveform_Fall, Driver_Waveform_Rise, Is_Buffer, Is_Inverter, Is_Flip_Flop, Is_Scan_Enabled_Flip_Flop, Condition_ID"),
        ("Input_Pins", "Input_Pins.csv", "Input_Pin_ID, Cell_ID, Input_Pin_Name, Clock, Capacitance, Fall_Capacitance, Rise_Capacitance, Max_Transition, Related_Power_Pin, Related_Ground_Pin"),
        ("Output_Pins", "Output_Pins.csv", "Output_Pin_ID, Cell_ID, Output_Pin_Name, Function, Max_Capacitance, Max_Transition, Power_Down_Function, Related_Power_Pin, Related_Ground_Pin"),
        ("Timing_Values", "Timing_Values.csv", "Timing_Value_ID, Cell_ID, Output_Pin_ID, Related_Input_Pin, Input_Transition, Output_Capacitance, Fall_Delay, Rise_Delay, Average_Delay, Fall_Transition, Rise_Transition")
    ]:
        csv_file_path = os.path.join(output_dir, file_name)
        import_csv_to_sql(conn, csv_file_path, table, columns)

    conn.commit()
    conn.close()
    print("Liberty processing and database population complete.")


if __name__ == '__main__':
    main()