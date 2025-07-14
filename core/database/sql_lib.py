""""Convert Liberty file to SQL database
"""
import os
import sys
import tqdm
import sqlite3
import argparse 

from config.pdks import get_scl, get_pdk_path, get_lib_paths
from config.sky130 import SCLVariants, View, get_sky130_pdk_path, get_sky130_lib_paths
from config.asap7nm import ASAP7nmSCLVariants, get_asap7nm_pdk_path, get_asap7nm_lib_paths
from core.parsers.lib.lib_parser import parse_liberty_file
from core.database.db_utils import delete_database


def insert_lib_data(conn, cells, operating_conditions, cell_varaint, separate_timing_tables=False, unified_timing_tables=True):
    """Inserts cell data into the database."""
    
    cursor = conn.cursor()
    
    # Insert the given operating condition into the 'OperatingConditions' table
    cursor.execute("""
        INSERT INTO Operating_Conditions (Name, Voltage, Process, Temperature, Tree_Type, Cell_Library) 
        VALUES (?, ?, ?, ?, ?, ?)""", 
        (operating_conditions['name'], operating_conditions['voltage'], operating_conditions['process'], operating_conditions['temperature'], 
        operating_conditions['tree_type'], cell_varaint)
    )

    cond_id = cursor.lastrowid
    

    for cell in tqdm.tqdm(cells): 
   
        cursor.execute("""
            INSERT INTO Cells (Name, Drive_Strength, Area, Cell_Footprint, Leakage_Power, Driver_Waveform_Fall, Driver_Waveform_Rise, Is_Buffer, Is_Inverter, Is_Flip_Flop, Is_Scan_Enabled_Flip_Flop,  Condition_ID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(cell['name']), cell['drive'], float(cell['area']), str(cell['cell_footprint']), float(cell['cell_leakage_power']), str(cell['driver_waveform_fall']), str(cell['driver_waveform_rise']), bool(cell['is_buffer']), bool(cell['is_inverter']), bool(cell['is_flip_flop']), bool(cell['is_scan_enabled_flip_flop']), cond_id))

        # Get the last inserted cell ID to use as foreign key for pins
        cell_id = cursor.lastrowid
        
        # Insert the pins data associated with this cell
        for pin in tqdm.tqdm(cell['pins']):
            if pin['direction'] == "input":
                is_clock = True if pin.get('clock', 'false').lower() == "true" else False
                related_power_pin = pin.get('related_power_pin', "")
                related_ground_pin =  pin.get('related_ground_pin', "")
                cursor.execute("""
                    INSERT INTO Input_Pins (Cell_ID, Input_Pin_Name, Clock, Capacitance, Fall_Capacitance, Rise_Capacitance, Max_Transition, Related_Power_Pin, Related_Ground_Pin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cell_id,
                    str(pin['name']),
                    bool(is_clock),
                    float(pin['capacitance']),
                    float(pin['fall_capacitance']) if 'fall_capacitance' in pin.keys() else None,
                    float(pin['rise_capacitance'])  if 'rise_capacitance' in pin.keys() else None,
                    float(pin['max_transition']) if 'max_transition' in pin.keys() else None,
                    str(related_power_pin),
                    str(related_ground_pin)
                ))
                
                pin_id = cursor.lastrowid

                # if 'internal_power' in pin.keys(): 
                #     for power_type in pin['internal_power'].keys(): 
                #         indicies =  pin['internal_power'][power_type]['index_1']
                #         values = pin['internal_power'][power_type]['values']
                                                
                #         for idx, value in zip(indicies, values):
                #             cursor.execute("""
                #             INSERT INTO Input_Pin_Internal_Powers (Input_Pin_ID, Power_Type, Index_1, Value)
                #             VALUES (?, ?, ?, ?)               
                #             """, (
                #                 pin_id, 
                #                 power_type,
                #                 idx, 
                #                 value
                #             )) 
                                    
            elif pin['direction'] == "output": 
                related_power_pin = pin.get('related_power_pin', "")
                related_ground_pin =  pin.get('related_ground_pin', "")
                cursor.execute("""
                    INSERT INTO Output_Pins (Cell_ID, Output_Pin_Name, Function, Max_Capacitance, Max_Transition, Power_Down_Function, Related_Power_Pin, Related_Ground_Pin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cell_id,
                    str(pin['name']),
                    str(pin.get('function', None)),
                    float(pin['max_capacitance']) if 'max_capacitance' in pin.keys() else None,
                    float(pin['max_transition']) if 'max_transition' in pin.keys() else None,
                    str(pin['power_down_function']) if 'power_down_function' in pin.keys() else None,
                    str(related_power_pin),
                    str(related_ground_pin)    
                ))
           
                pin_id = cursor.lastrowid

            if 'timing' in pin.keys():
                for related_pin in tqdm.tqdm(pin['timing'].keys()):
                    if unified_timing_tables: 
                        for row in pin['timing'][related_pin]: 
                            cursor.execute("""
                            INSERT INTO Timing_Values (Cell_ID, Output_Pin_ID, Related_Input_Pin, Input_Transition, Output_Capacitance, Fall_Delay, Rise_Delay, Average_Delay, Fall_Transition, Rise_Transition)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                cell_id,
                                pin_id,
                                str(related_pin),
                                float(row['index_1']),
                                float(row['index_2']),
                                float(row['fall_delay']),
                                float(row['rise_delay']),
                                float(row['average_delay']),
                                float(row['fall_transition']),
                                float(row['rise_transition']),
                            ))
                    else: 
                        for timing_type, table in tqdm.tqdm(pin['timing'][related_pin].items()):
                            cursor.execute("""
                            INSERT INTO Timing_Tables (Output_Pin_ID, Timing_Type, Related_Input_Pin, Index_1_Label, Index_2_Label)
                            VALUES (?, ?, ?, ?, ?)
                            """, (
                                pin_id,
                                str(timing_type),
                                str(related_pin),
                                str(table['index_1_label']),
                                str(table['index_2_label'])
                            ))
    
                            timing_id = cursor.lastrowid

                            rows = len(table['data'])
                            cols = len(table['data'][0])
                            for i in range(len(table['index_1'][0])):
                                for j in range(len(table['index_2'][0])):
                                    index_1_value = table['index_1'][0][i]
                                    index_2_value = table['index_2'][0][j]                                
                                    if j < rows and i < cols:
                                        timing_value =  table['data'][j][i]

                                        cursor.execute("""
                                            INSERT INTO Timing_Table_Values (Timing_Table_ID, Index_1, Index_2, Value)
                                            VALUES (?, ?, ?, ?)
                                        """, (
                                            timing_id,
                                            float(index_1_value),
                                            float(index_2_value),
                                            float(timing_value)
                                        ))
                                    # else:
                                    #     print(f"Warning: Indices out of bounds: j={j}, i={i}. Skipping this entry.")

    conn.commit()


def create_lib_tables(conn, partition=False):
    
    cursor = conn.cursor()
    
    # Create the OperatingConditions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Operating_Conditions (
        Condition_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Voltage REAL,
        Process REAL,
        Temperature REAL,
        Tree_Type TEXT,
        Cell_Library TEXT  --Cell Library Column
    );
    """)

    # Create the Cells table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cells (
        Cell_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Drive_Strength INTEGER,
        Area REAL,
        Cell_Footprint TEXT,
        Leakage_Power REAL,
        Driver_Waveform_Fall TEXT,
        Driver_Waveform_Rise TEXT,
        Is_Buffer BOOLEAN,
        Is_Inverter BOOLEAN,
        Is_Flip_Flop BOOLEAN,
        Is_Scan_Enabled_Flip_Flop BOOLEAN,                     
        Condition_ID INTEGER,
        FOREIGN KEY (Condition_ID) REFERENCES Operating_Conditions (Condition_ID)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Input_Pins (
        Input_Pin_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Cell_ID INTEGER,
        Input_Pin_Name TEXT,
        Clock BOOLEAN,
        Capacitance REAL,
        Fall_Capacitance REAL,
        Rise_Capacitance REAL,
        Max_Transition REAL,
        Related_Power_Pin TEXT,
        Related_Ground_Pin TEXT,
        FOREIGN KEY (Cell_ID) REFERENCES Cells (Cell_ID)
    );                       
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Output_Pins (
        Output_Pin_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Cell_ID INTEGER,
        Output_Pin_Name TEXT,
        Function TEXT,
        Max_Capacitance REAL,
        Max_Transition REAL,
        Power_Down_Function TEXT,
        Related_Power_Pin TEXT,
        Related_Ground_Pin TEXT,
        FOREIGN KEY (Cell_ID) REFERENCES Cells (Cell_ID)
    );                
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Input_Pin_Internal_Powers (
        Internal_Power_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Input_Pin_ID INTEGER,
        Power_Type TEXT,  -- This will be either 'fall' or 'rise'
        Index_1 REAL,     -- This will store individual index_1 values
        Value REAL,       -- This will store the corresponding power values
        FOREIGN KEY (Input_Pin_ID) REFERENCES Input_Pins (Input_Pin_ID)
    );       
    """)
    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Timing_Values  (
        Timing_Value_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Cell_ID INTEGER,             -- Foreign key referencing the cell
        Output_Pin_ID INTEGER,       -- Foreign key referencing the output pin
        Related_Input_Pin TEXT,      -- Name of the input pin
        Input_Transition REAL,       -- The first index dimension (input transition)
        Output_Capacitance REAL,     -- The second index dimension (output capacitance)
        Fall_Delay REAL,             -- Fall propagation delay value
        Rise_Delay REAL,             -- Rise propagation delay value
        Average_Delay REAL,          -- Average propagation delay value
        Fall_Transition REAL,        -- Fall transition time value
        Rise_Transition REAL,        -- Rise transition time value
        FOREIGN KEY (Cell_ID) REFERENCES Cells (Cell_ID),
        FOREIGN KEY (Output_Pin_ID) REFERENCES Output_Pins (Output_Pin_ID)
    );            
    """)
    
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_op_cond_id ON Operating_Conditions (Condition_ID);",
        "CREATE INDEX IF NOT EXISTS idx_op_cond_volt ON Operating_Conditions (Voltage);",
        "CREATE INDEX IF NOT EXISTS idx_op_cond_temp ON Operating_Conditions (Temperature);",
        "CREATE INDEX IF NOT EXISTS idx_op_cond_cell_lib ON Operating_Conditions (Cell_Library);",
        "CREATE INDEX IF NOT EXISTS idx_cell_id ON Cells (Cell_ID);",
        "CREATE INDEX IF NOT EXISTS idx_cell_name ON Cells (Name);",
        "CREATE INDEX IF NOT EXISTS idx_cell_cond_id ON Cells (Condition_ID);",
        "CREATE INDEX IF NOT EXISTS idx_input_pin_id ON Input_Pins (Input_Pin_ID);",
        "CREATE INDEX IF NOT EXISTS idx_input_pin_name ON Input_Pins (Input_Pin_Name);",
        "CREATE INDEX IF NOT EXISTS idx_input_pin_cell_id ON Input_Pins (Cell_ID);",
        "CREATE INDEX IF NOT EXISTS idx_output_pin_id ON Output_Pins (Output_Pin_ID);",
        "CREATE INDEX IF NOT EXISTS idx_output_pin_name ON Output_Pins (Output_Pin_Name);",
        "CREATE INDEX IF NOT EXISTS idx_output_pin_cell_id ON Output_Pins (Cell_ID);",
        "CREATE INDEX IF NOT EXISTS idx_timing_val_id ON Timing_Values (Timing_Value_ID);",
        "CREATE INDEX IF NOT EXISTS idx_timing_cell_id ON Timing_Values (Cell_ID);",
        "CREATE INDEX IF NOT EXISTS idx_timing_output_pin_id ON Timing_Values (Output_Pin_ID);",
        "CREATE INDEX IF NOT EXISTS idx_timing_related_input_pin ON Timing_Values (Related_Input_Pin);",
    ]

    for query in index_queries:
        cursor.execute(query)

    conn.commit()


def get_lib_description(selected_schema=None, partition=False):
    """Returns the description of the tables in the selected schema
    """

#    (Name, name of this operating condition. Value examples: [tt_025C_1v80, ff_100C_1v65, ss_100C_1v60]),

    op_cond_table = """
# Table: Operating_Conditions
This table specifies the operating conditions (temperature, voltage) for the different standard cell libraries, it has the following columns: 
[
    (Condition_ID, id of the operating condition. Value examples: [1, 2, 3, 4])
    (Voltage, voltage value. Value examples: [1.65, 1.95, 1.76, 1.8]),
    (Process, process number. Value examples: [1.0] ),
    (Temperature, temperature value. Value examples: [100.0, 25.0, -40] ),
    (Tree_Type, tree type. Value examples: [balanced_tree] ),
    (Cell_Library, standard cell library. Value examples: [sky130_fd_sc_hdll, sky130_fd_sc_hd, sky130_fd_sc_hs, sky130_fd_sc_ms, sky130_fd_sc_ls, sky130_fd_sc_lp])
]
"""
    cells_table = """
# Table: Cells
This table contains information about the different cells, it has the following columns:
[
    (Cell_ID, the id of the cell. Value examples: [372, 256, 1, 2]),
    (Condition_ID, the unique identifier for the operating condtion this entry is associate with. Value examples: [1, 2, 3, 4]),
    (Name, name of the cell. Value examples: [sky130_fd_sc_hd__or4bb_4, sky130_fd_sc_hd__xor3_1, sky130_fd_sc_hd__or2b_1]),
    (Drive_Strength, specifies the drive strength of the cells. Value examples: [1, 2, 4]),
    (Area, area of the cell. Value examples: [16.2656 , 27.5264 , 8.7584 , 7.5072]),
    (Leakage_Power, leakage power of the cell. Value examples: [2.108477 , 2.960486 , 3.827329 , 3.252294]),
    (Cell_Footprint, footprint name of the cell. Value examples: [sky130_fd_sc_hd__or3_4, sky130_fd_sc_hd__or4, sky130_fd_sc_hd__nor4b]),
    (Driver_Waveform_Fall, driver fall waveform. Value examples: [ramp]),
    (Driver_Waveform_Rise, driver rise waveform. Value examples: [ramp]),
    (Is_Buffer, specifies whether cell is a buffer cell or not. Value examples: [True, False]),
    (Is_Inverter, specifies whether cell is an inverter cell or not. Value examples: [True, False]),
    (Is_Flip_Flop, specifies whether cell is a flip-flop cell or not. Value examples: [True, False]),
    (Is_Scan_Enabled_Flip_Flop, specifies whether cell is a scan enabled flip-flop  cell or not. Value examples: [True, False]),
]
"""
    if partition: 
        cells_table = """
# Table: Cells
This table contains information about the different cells, it has the following columns:
[
    (Cell_ID, the id of the cell. Value examples: [372, 256, 1, 2]),
    (Name, name of the cell. Value examples: [sky130_fd_sc_hd__or4bb_4, sky130_fd_sc_hd__xor3_1, sky130_fd_sc_hd__or2b_1]),
    (Drive_Strength, specifies the drive strength of the cells. Value examples: [1, 2, 4]),
    (Area, area of the cell. Value examples: [16.2656 , 27.5264 , 8.7584 , 7.5072]),
    (Leakage_Power, leakage power of the cell. Value examples: [2.108477 , 2.960486 , 3.827329 , 3.252294]),
    (Cell_Footprint, footprint name of the cell. Value examples: [sky130_fd_sc_hd__or3_4, sky130_fd_sc_hd__or4, sky130_fd_sc_hd__nor4b]),
    (Driver_Waveform_Fall, driver fall waveform. Value examples: [ramp]),
    (Driver_Waveform_Rise, driver rise waveform. Value examples: [ramp]),
    (Is_Buffer, specifies whether cell is a buffer cell or not. Value examples: [True, False]),
    (Is_Inverter, specifies whether cell is an inverter cell or not. Value examples: [True, False]),
    (Is_Flip_Flop, specifies whether cell is a flip-flop cell or not. Value examples: [True, False]),
    (Is_Scan_Enabled_Flip_Flop, specifies whether cell is a scan enabled flip-flop  cell or not. Value examples: [True, False]),
]
"""
    else: 
        cells_table = """
# Table: Cells
This table contains information about the different cells, it has the following columns:
[
    (Cell_ID, the id of the cell. Value examples: [372, 256, 1, 2]),
    (Condition_ID, the unique identifier for the operating condtion this entry is associate with. Value examples: [1, 2, 3, 4]),
    (Name, name of the cell. Value examples: [sky130_fd_sc_hd__or4bb_4, sky130_fd_sc_hd__xor3_1, sky130_fd_sc_hd__o221a_4]),
    (Drive_Strength, specifies the drive strength of the cells. Value examples: [1, 2, 4]),
    (Area, area of the cell. Value examples: [16.2656 , 27.5264 , 8.7584 , 7.5072]),
    (Leakage_Power, leakage power of the cell. Value examples: [2.108477 , 2.960486 , 3.827329 , 3.252294]),
    (Cell_Footprint, footprint name of the cell. Value examples: [sky130_fd_sc_hd__or4bb_4, sky130_fd_sc_hd__o221a_4, sky130_fd_sc_hd__nor4b]),
    (Driver_Waveform_Fall, driver fall waveform. Value examples: [ramp]),
    (Driver_Waveform_Rise, driver rise waveform. Value examples: [ramp]),
    (Is_Buffer, specifies whether cell is a buffer cell or not. Value examples: [True, False]),
    (Is_Inverter, specifies whether cell is an inverter cell or not. Value examples: [True, False]),
    (Is_Flip_Flop, specifies whether cell is a flip-flop cell or not. Value examples: [True, False]),
    (Is_Scan_Enabled_Flip_Flop, specifies whether cell is a scan enabled flip-flop  cell or not. Value examples: [True, False]),
]
"""
    input_pins_table = """
# Table: Input_Pins 
This table contains information about the input pins for each cell in the Cells table. It has the following columns:
[
    (Input_Pin_ID, the unique identifier for the input pin. Value examples: [1701, 598, 1, 4, 6]),
    (Cell_ID, the unique identifier for the cell to which this pin belongs, referencing the Cells table. Value examples: [1, 2, 370, 255]),
    (Input_Pin_Name, the name of the input pin, typically representing its function or position within the cell. Value examples: [A, B, C, A1, CLK]),
    (Clock, a Boolean value specifying whether the pin is a clock pin. True indicates it is a clock pin; False indicates it is not. Value examples: [False, True]. This is a boolean type variable NOT a string),
    (Capacitance, the total capacitance of the input pin, measured in farads. This value affects the speed and power consumption of the cell. Value examples: [0.001765, 0.003292, 0.008679, 0.008259]),
    (Fall_Capacitance, the capacitance of the input pin when the signal is falling (transitioning from high to low). This value impacts the fall time of the signal. Value examples: [0.002321, 0.002188, 0.002291]),
    (Rise_Capacitance, the capacitance of the input pin when the signal is rising (transitioning from low to high). This value impacts the rise time of the signal. Value examples: [0.002621, 0.004756, 0.00255]),
    (Related_Power_Pin, the name of the power pin that provides the supply voltage for the input pin. Value examples: [VPWR]),
    (Related_Ground_Pin, the name of the ground pin that provides the reference ground for the input pin. Value examples: [VGND]),
]
"""
        
    output_pins_table = """
# Table: Output_Pins 
This table contains information about the output pins for each cell in the Cells table. It has the following columns:
[
    (Output_Pin_ID, the unique identifier for the output pin. Value examples: [1701, 598, 1, 4, 6]),
    (Cell_ID, the unique identifier for the cell to which this pin belongs, referencing the Cells table. Value examples: [1, 2, 370, 255]),
    (Output_Pin_Name, the name of the output pin, typically representing its function or position within the cell. Value examples: [A, B, C, X]),
    (Function, the boolean function of the output pin, describing its logic behavior. Value examples: [(!A&!B) | (A&B), (A&!B) | (!A&B)]),
    (Max_Capacitance, the maximum capacitance that the output pin can drive. Defines the drive strenght of the cell. This value impacts the load the pin can handle. Value examples: [0.175791, 0.324107, 0.535593]),
    (Max_Transition, the maximum transition time of the output pin. This value affects the signal integrity and speed. Value examples: [1.499941, 1.502465, 1.496226]),
    (Related_Power_Pin, the name of the power pin that provides the supply voltage for the output pin. Value examples: [VPWR]),
    (Related_Ground_Pin, the name of the ground pin that provides the reference ground for the output pin. Value examples: [VGND]),
    (Power_Down_Function, the boolean function of the output pin when powered down, indicating its state during power-down conditions. Value examples: [(!VPWR + VGND)]),
]
"""
    
    timing_tables = """
# Table Timing_Values
This table stores the average propagation delay values, computed as the average of rise and fall delays for each combination of index parameters.
[
    (Timing_Value_ID, Unique identifier for each timing value entry. This is an auto-incremented integer. Example values: [1, 2, 3]),
    (Cell_ID, The unique identifier of the cell to which this timing data is associated. It references the `Cells` table. Example values: [1001, 1002, 1003]),
    (Output_Pin_ID, The unique identifier of the output pin associated with the timing data. It references the `Output_Pins` table. Example values: [2001, 2002, 2003]),
    (Related_Input_Pin, The name of the input pin that drives the output pin and is related to this timing entry. Example values: [A, B, CLK, IN]),
    (Input_Transition, The input net transition value representing the rate of change in the input signal. This is the first index dimension of the timing table. Example values: [0.010, 0.050, 0.100]),
    (Output_Capacitance, The total output net capacitance connected to the output pin. This is the second index dimension of the timing table. Example values: [0.001, 0.005, 0.010]),
    (Fall_Delay, The fall propagation delay, representing the time it takes for the signal to fall (transition from high to low) from the input to the output pin. Example values: [0.100, 0.150, 0.200]),
    (Rise_Delay, The rise propagation delay, representing the time it takes for the signal to rise (transition from low to high) from the input to the output pin. Example values: [0.120, 0.170, 0.220]),
    (Average_Delay, The average propagation delay, computed as the average of the rise and fall delays for the same input transition and output capacitance conditions. Example values: [0.110, 0.160, 0.210]),
    (Fall_Transition, The fall transition time, which indicates the time taken for the output signal to transition from high to low. Example values: [0.030, 0.040, 0.050]),
    (Rise_Transition, The rise transition time, which indicates the time taken for the output signal to transition from low to high. Example values: [0.035, 0.045, 0.055])
]
"""

    desc = """The liberty file database contains information about the different standard cell libraries under different operating conditions.
    It has the following tables: \n"""
 
    if selected_schema: 
        if 'Operating_Conditions' in selected_schema: 
            desc += op_cond_table
        
        if 'Cells' in selected_schema: 
            desc += cells_table

        if 'Input_Pins' in selected_schema: 
            desc += input_pins_table 
            
        if 'Output_Pins' in selected_schema: 
            desc += output_pins_table 
        
        if 'Timing_Values' in selected_schema: 
            desc += timing_tables
    
    else:
        if partition: 
            desc = cells_table + input_pins_table + output_pins_table + timing_tables 
        else: 
            desc = op_cond_table + cells_table + input_pins_table + output_pins_table + timing_tables 
         
    return desc 


def get_lib_foreign_keys(selected_schema, partition=False):
    
    if selected_schema != None: 
        cells_operating_cond = 'Cells.`Condition_ID` = Operating_Conditions.`Condition_ID`\n'
        cells_input_pins = 'Cells.`Cell_ID` = Input_Pins.`Cell_ID` \n'
        cells_output_pins = 'Cells.`Cell_ID` =  Output_Pins.`Cell_ID` \n'
        output_pin_timing_tables = 'Output_Pins.`Output_Pin_ID` = Timing_Tables.`Output_Pin_ID`\n'
        timing_values = """
Timing_Values.`Cell_ID` = Cells.`Cell_ID`
Timing_Values.`Output_Pin_ID` = Output_Pins.`Output_Pin_ID`
"""
        
        fk_str = ""
        
        if not partition: 
            if set(['Cells', 'Operating_Conditions']).issubset(set(selected_schema)): 
                fk_str += cells_operating_cond
            
        if set(['Cells', 'Input_Pins']).issubset(set(selected_schema)): 
            fk_str += cells_input_pins

        if set(['Cells', 'Output_Pins']).issubset(set(selected_schema)): 
            fk_str += cells_output_pins

        if set(['Output_Pins', 'Timing_Tables']).issubset(set(selected_schema)): 
            fk_str += output_pin_timing_tables
        
        if set(['Timing_Values']).issubset(set(selected_schema)): 
            fk_str += timing_values    
    else: 
        if partition: 
            fk_str = """
Cells.`Cell_ID` = Input_Pins.`Cell_ID` 
Cells.`Cell_ID` = Output_Pins.`Cell_ID`
Output_Pins.`Output_Pin_ID` = Timing_Tables.`Output_Pin_ID`
Timing_Values.`Cell_ID` = Cells.`Cell_ID`
Timing_Values.`Output_Pin_ID` = Output_Pins.`Output_Pin_ID`
"""
        else: 
            fk_str = """
Operating_Conditions.`Condition_ID` = Cells.`Condition_ID` 
Cells.`Cell_ID` = Input_Pins.`Cell_ID` 
Cells.`Cell_ID` = Output_Pins.`Cell_ID`
Output_Pins.`Output_Pin_ID` = Timing_Tables.`Output_Pin_ID`
Timing_Values.`Cell_ID` = Cells.`Cell_ID`
Timing_Values.`Output_Pin_ID` = Output_Pins.`Output_Pin_ID`
"""
    return fk_str


def get_lib_table_names(partition=False):
    if partition: 
        table_names = [
            "Cells",
            "Input_Pins",
            "Output_Pins",
            "Input_Pin_Internal_Powers",
            "Timing_Values"
        ]
    else: 
        table_names = [
            "Operating_Conditions",
            "Cells",
            "Input_Pins",
            "Output_Pins",
            "Input_Pin_Internal_Powers",
            "Timing_Values"
        ]

    return table_names 



def drop_cell_library_corner_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Cells_Temp (
            Cell_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Drive_Strength INTEGER,
            Area REAL,
            Cell_Footprint TEXT,
            Leakage_Power REAL,
            Driver_Waveform_Fall TEXT,
            Driver_Waveform_Rise TEXT,
            Is_Buffer BOOLEAN,
            Is_Inverter BOOLEAN,
            Is_Flip_Flop BOOLEAN,
            Is_Scan_Enabled_Flip_Flop BOOLEAN
        );
    """)
    cursor.execute("""
        INSERT INTO Cells_Temp (
            Cell_ID, Name, Drive_Strength, Area, Cell_Footprint, 
            Leakage_Power, Driver_Waveform_Fall, Driver_Waveform_Rise, 
            Is_Buffer, Is_Inverter, Is_Flip_Flop, Is_Scan_Enabled_Flip_Flop
        )
        SELECT 
            Cell_ID, Name, Drive_Strength, Area, Cell_Footprint, 
            Leakage_Power, Driver_Waveform_Fall, Driver_Waveform_Rise, 
            Is_Buffer, Is_Inverter, Is_Flip_Flop, Is_Scan_Enabled_Flip_Flop
        FROM Cells;
    """)
    cursor.execute("DROP TABLE Cells;")
    cursor.execute("ALTER TABLE Cells_Temp RENAME TO Cells;")
    cursor.execute("DROP TABLE IF EXISTS Operating_Conditions;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
 


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

    scl_variants = get_scl(pdk_name)
   
    db_conn = dict()

    if not partition:
        conn = sqlite3.connect(":memory:")
        db_conn["single"] = conn
        create_lib_tables(conn)

    if partition:
        for variant in tqdm.tqdm(scl_variants):
            lib_path = get_lib_paths(pdk_name, variant=variant.value)
            for corner in tqdm.tqdm(os.listdir(lib_path)):
                db_conn[f"{variant.value}_{corner}"] = sqlite3.connect(":memory:")  
                create_lib_tables(db_conn[f"{variant.value}_{corner}"])

    for variant in tqdm.tqdm(scl_variants):
        lib_path = get_lib_paths(pdk_name, variant.value)
        
        for corner in tqdm.tqdm(os.listdir(lib_path)):
            if 'ccsnoise' in corner or 'pwrlkg' in corner or 'ka1v76' in corner or ".db" in corner or os.path.splitext(corner)[1] != ".lib" :  # Ignore certain corners
                continue
            
            print("Running Corner: ", corner)
            corner_path = os.path.join(lib_path, corner)
            print(corner_path)
            
            cells, operating_conditions = parse_liberty_file(corner_path)

            if partition:
                insert_lib_data(db_conn[f"{variant.value}_{corner}"], cells, operating_conditions, cell_varaint=variant.value)
                drop_cell_library_corner_column(db_conn[f"{variant.value}_{corner}"])
            else:
                insert_lib_data(db_conn["single"], cells, operating_conditions, cell_varaint=variant.value)

    if partition:
        for key, conn in db_conn.items():
            variant_name, corner = key.split('_', 1)
            disk_db_path = os.path.join(output_dir, f'{pdk_name}_lib_{variant_name}_{corner}.db')
            with sqlite3.connect(disk_db_path) as disk_conn:
                conn.backup(disk_conn)
    else:
        disk_db_path = os.path.join(output_dir, f'{pdk_name}_lib.db')
        with sqlite3.connect(disk_db_path) as disk_conn:
            db_conn["single"].backup(disk_conn)

    for conn in db_conn.values():
        conn.commit()
        conn.close()


if __name__ == '__main__':
    main()