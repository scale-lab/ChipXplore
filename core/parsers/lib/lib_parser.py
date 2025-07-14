"""Parse liberty files
"""

import re 
import sys 
from liberty.parser import parse_liberty
from liberty.types import *

BUF_MARKER ='buf'
INV_MARKER = 'inv'
FF_MARKER = 'df'


def is_buf(name):
    if BUF_MARKER in name.lower():
        return True
    return False 


def is_inv(name):
    if BUF_MARKER in name.lower():
        return True
    return False  


def is_ff(name):
    if FF_MARKER in name.lower():
        return True
    return False  
 

def get_drive_strength(name):
    parts = name.split("__")
    if len(parts) > 1:
        gate_part = parts[-1]
        for char in reversed(gate_part):
            if char.isdigit():
                return int(char)
    
    return None 


def create_unified_timing_table(timing_tables):
    index_1_consistent = all(np.array_equal(timing_tables[type]['index_1'], timing_tables['cell_fall']['index_1']) for type in ['cell_rise', 'fall_transition', 'rise_transition'])
    index_2_consistent = all(np.array_equal(timing_tables[type]['index_2'], timing_tables['cell_fall']['index_2']) for type in ['cell_rise', 'fall_transition', 'rise_transition'])
    
    if not (index_1_consistent and index_2_consistent):
        print("Inconsistent index_1 or index_2 values across timing tables")
        sys.exit(0)
        # raise ValueError("Inconsistent index_1 or index_2 values across timing tables")
    
    if 'average_delay' not in timing_tables:
        timing_tables['average_delay'] = (timing_tables['cell_fall']['data'] + timing_tables['cell_rise']['data']) / 2

    unified_timing_table = []
    
    index_1 = timing_tables['cell_fall']['index_1'][0]
    index_2 = timing_tables['cell_fall']['index_2'][0]
    
    rows = len(timing_tables['cell_fall']['data'])
    cols = len(timing_tables['cell_fall']['data'][0])

    for i, idx_1 in enumerate(index_1):
        for j, idx_2 in enumerate(index_2):
            if j < cols  and i < rows:
                row = {
                    'index_1': idx_1,
                    'index_2': idx_2,
                    'fall_delay': timing_tables['cell_fall']['data'][i][j],
                    'rise_delay': timing_tables['cell_rise']['data'][i][j],
                    'average_delay': timing_tables['average_delay']['data'][i][j],
                    'fall_transition': timing_tables['fall_transition']['data'][i][j],
                    'rise_transition': timing_tables['rise_transition']['data'][i][j],
                    'index_1_label': timing_tables['cell_fall']['index_1_label'],
                    'index_2_label': timing_tables['cell_fall']['index_2_label'],
                    'timing_sense': timing_tables['cell_fall']['timing_sense'],
                    'timing_type': timing_tables['cell_fall']['timing_type']
                }
                unified_timing_table.append(row)
            else:
               print(f"Warning: Indices out of bounds: j={j}, i={i}. Skipping this entry.")

    return unified_timing_table

def parse_liberty_file(liberty_file):
    """Parses a Liberty file and extracts cell data."""
    # Replace all occurrences of !VAR in 'when' conditions
    with open(liberty_file, "r") as f:
        data = f.read()

    fixed_data = re.sub(r'leakage_power\s*\(\)\s*\{.*?\}', '', data, flags=re.DOTALL)

    library = parse_liberty(fixed_data)
    time_unit_str = library['time_unit'].value
    cap_unit_str = library['capacitive_load_unit']
    voltage_unit = library['voltage_unit']
    leakage_power_unit = library['leakage_power_unit']
    current_unit = library['current_unit']
    pulling_resistance_unit = library['pulling_resistance_unit']
    op_cond = library.get_groups("operating_conditions")[0]

    if type(op_cond.args[0]) == str: 
        operating_conditions = {'name': op_cond.args[0]}
    else: 
        operating_conditions = {'name': op_cond.args[0].value}
    
    for attribute in op_cond.attributes:
        if isinstance(attribute.value, EscapedString):
            operating_conditions[attribute.name] = attribute.value.value
        else:
            operating_conditions[attribute.name] = attribute.value

    if 'tree_type' not in operating_conditions.keys():
        operating_conditions['tree_type'] = ""

    # Notice that different formats are used for both units.
    print(f"time_unit_str = {time_unit_str}")
    print(f"cap_unit_str = {cap_unit_str}")

    cells_data = []
   
    # Loop through all cells.
    for cell_group in library.get_groups('cell'):
        pins = []

        if type(cell_group.args[0]) != str: 
            name = cell_group.args[0].value
        else: 
            name = cell_group.args[0]

        is_buffer = is_buf(name)
        is_inverter = is_inv(name)
        is_flip_flop = is_ff(name)

        drive = get_drive_strength(name)

        cell = {
            'name': name, 
            'area': 0.0, 
            'drive': drive,
            'cell_footprint': '', 
            'cell_leakage_power': 0.0, 
            'driver_waveform_fall': '', 
            'driver_waveform_rise': '',
            'is_buffer': is_buffer,
            'is_inverter': is_inverter,
            'is_sequential': False,
            'is_flip_flop': is_flip_flop,
            'is_scan_enabled_flip_flop': False
        }
        
        for attribute in cell_group.attributes:
            if isinstance(attribute.value, EscapedString):
                cell[attribute.name] = attribute.value.value
            else:
                cell[attribute.name] = attribute.value 

        
        # Loop through all pins of the cell.
        input_pins = []
        output_pins = [] 
        
        internal_power_tables_input_pins = {}
        internal_power_tables_output_pins = {}
        
        for pin_group in cell_group.get_groups('pin'):

            if type(pin_group.args[0]) != str: 
                pin_name = pin_group.args[0].value
            else:
                pin_name = pin_group.args[0]

            pin = {'name': pin_name}
            for attribute in pin_group.attributes:
                if isinstance(attribute.value, EscapedString):
                    pin[attribute.name] = attribute.value.value
                else:
                    pin[attribute.name] = attribute.value
            
            has_clock_pin = True if pin.get('clock', 'false').lower() == "true" else False
            cell['is_sequential'] = has_clock_pin 

            cell['is_scan_enabled_flip_flop'] = True if 'SCE' in pin_name else False 

            if pin['direction'] == 'output':
               output_pins.append(pin['name'])
            else:
                input_pins.append(pin['name'])
                # get internal power tables 
                internal_power = pin_group.get_groups('internal_power')
                # if len(internal_power) != 0:
                #     fall_power = internal_power[0].get_groups('fall_power')
                #     fall_power_index_1 = fall_power[0].get_array('index_1')[0]
                #     fall_power_values = fall_power[0].get_array('values')[0]

                #     rise_power = internal_power[0].get_groups('rise_power')
                #     # rise_power_index_1 = rise_power[0].get_array('index_1')[0]
                #     # rise_power_values = rise_power[0].get_array('values')[0]

                #     # internal_power_tables_input_pins[pin_name] = {
                #     #     'fall_power':{
                #     #         'index_1': fall_power_index_1,
                #     #         'values': fall_power_values
                #     #     },
                #     #     'rise_power': {
                #     #         'index_1': rise_power_index_1,
                #     #         'values': rise_power_values
                #     #     }
                #     # }

            pins.append(pin)
 
        # get timing tables
        timing_tables_output_pins = {}
        if len(input_pins) != 0 and len(output_pins) != 0:
            for output_pin in output_pins: 
                out_pin = select_pin(cell_group, output_pin)
                timing_tables_bypinn = {}
                for in_pin in input_pins:
                    try: 
                        timing_tables = {}
                        for table_type in ['cell_fall', 'cell_rise', 'fall_transition', 'rise_transition']: 
                            table = select_timing_table(out_pin, related_pin=in_pin, table_name=table_type)
                            
                            timing_sense = table.get_groups('timing_sense')
                            timing_type = table.get_groups('timing_type')
                            index_1 = table.get_array('index_1')
                            try: 
                                index_2 = table.get_array('index_2')
                            except: 
                                index_2 = index_1 

                            data = table.get_array('values')
                            
                            # Find out which index is the output load and which the input slew.
                            template_name = table.args[0]
                            template = library.get_group('lu_table_template', template_name)

                            if type(template['variable_1']) != str:
                                index_1_label = template['variable_1'].value
                                index_2_label = template['variable_2'].value
                            else:
                                index_1_label = template['variable_1']
                                index_2_label = template['variable_2']
                            
                            timing_tables[table_type] = {'index_1': index_1, 'index_2': index_2, 'data': data, 
                                                   'index_1_label': index_1_label, 'index_2_label': index_2_label,
                                                   'timing_sense': timing_sense, 'timing_type': timing_type}
                        
                        # compute average delay
                        average_delay = (timing_tables['cell_fall']['data'] + timing_tables['cell_rise']['data']) / 2
                        average_prop_delay = {
                            'index_1': timing_tables['cell_fall']['index_1'],
                            'index_2': timing_tables['cell_fall']['index_2'],
                            'index_1_label': timing_tables['cell_fall']['index_1_label'], 
                            'index_2_label': timing_tables['cell_fall']['index_2_label'], 
                            'timing_sense': timing_tables['cell_fall']['timing_sense'], 
                            'timing_type': timing_tables['cell_fall']['timing_type'], 
                            'data': average_delay
                        }
                        timing_tables['average_delay'] = average_prop_delay

                        # compute average transition
                        average_transition = (timing_tables['rise_transition']['data'] + timing_tables['fall_transition']['data']) / 2
                        average_transition_table = {
                            'index_1': timing_tables['rise_transition']['index_1'],
                            'index_2': timing_tables['rise_transition']['index_2'],
                            'index_1_label': timing_tables['rise_transition']['index_1_label'], 
                            'index_2_label': timing_tables['rise_transition']['index_2_label'], 
                            'timing_sense': timing_tables['rise_transition']['timing_sense'], 
                            'timing_type': timing_tables['rise_transition']['timing_type'], 
                            'data': average_transition
                        }
                        timing_tables['average_transition'] = average_transition_table
                        unified_timing_tables = create_unified_timing_table(timing_tables)
                        timing_tables_bypinn[in_pin] = unified_timing_tables
                    except (KeyError, ValueError) as e: 
                        print(f"Got Error {e}, output pins {output_pins}, input pins: {input_pins}, cell {name}")

                timing_tables_output_pins[output_pin] = timing_tables_bypinn
      
            # get internal power tables

        for pin in pins: 
            name = pin['name']
            if pin['direction'] == 'output' and name in timing_tables_output_pins.keys():
                pin['timing'] = timing_tables_output_pins[name]
            if pin['direction'] == 'input' and name in internal_power_tables_input_pins.keys():
                pin['internal_power'] = internal_power_tables_input_pins[name]
            # elif pin['direction'] == 'output':
            #     pin['internal_power'] = internal_power_tables_output_pins[name]
        
        cell['pins'] = pins
        cells_data.append(cell)    
    
    return cells_data, operating_conditions  


__all__ = [
    'parse_liberty_file'
]


def main():
    lib_path = '/oscar/data/sreda/mabdelat/.volare/volare/sky130/versions/bdc9412b3e468c102d01b7cf6337be06ec6e9c9a/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
    
    parse_liberty_file(
        liberty_file=lib_path
    ) 

if __name__ == '__main__':
    main()

