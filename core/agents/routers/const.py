lib_template = """
    // Start of a cell definition
    cell (\"<cell_name>\") {{
        // Leakage power information for different conditions
        leakage_power () {{
            value : <leakage_power_value>;  // The leakage power value
            when : \"<condition>\";  // The condition under which this leakage power value applies
        }}
        // Repeat leakage_power blocks as needed for different conditions

        // Cell area information
        area : <area_value>;  // The physical area of the cell

        // Cell footprint
        cell_footprint : \"<cell_footprint>\";  // The footprint name of the cell

        // Total cell leakage power
        Leakage_Power : <cell_leakage_power_value>;  // The total leakage power of the cell

        // Driver waveform information
        driver_waveform_fall : \"<driver_waveform_fall>\";  // The falling waveform type
        driver_waveform_rise : \"<driver_waveform_rise>\";  // The rising waveform type

        // Input Pin information
        pin (\"<pin_name>\") {{
            capacitance : <capacitance_value>;  // The capacitance of the pin
            clock : \"<true_or_false>\";  // Specifies whether this input pin is a clock pin or not
            direction : \"<input_or_output>\";  // The direction of the pin (input or output)
            fall_capacitance : <fall_capacitance_value>;  // The fall capacitance of the pin
            internal_power () {{
                fall_power (\"<fall_power_group>\") {{
                    index_1(\"<index_values>\");  // Index values for fall power
                    values(\"<values>\");  // Fall power values
                }}
                rise_power (\"<rise_power_group>\") {{
                    index_1(\"<index_values>\");  // Index values for rise power
                    values(\"<values>\");  // Rise power values
                }}
            }}
            max_transition : <max_transition_value>;  // The maximum transition time for the pin
            related_ground_pin : \"<related_ground_pin>\";  // The related ground pin
            related_power_pin : \"<related_power_pin>\";  // The related power pin
            rise_capacitance : <rise_capacitance_value>;  // The rise capacitance of the pin
        }}
        
        // Repeat pin blocks as needed for each pin

        // Output pin information (example for an output pin with a function)
        pin (\"<pin_name>\") {{
            direction : \"<input_or_output>\";  // The direction of the pin (input or output)
            function : \"<function>\";  // The boolean function of the output pin
            internal_power () {{
                fall_power (\"<fall_power_group>\") {{
                    index_1(\"<index_values>\");  // Index values for fall power
                    index_2(\"<index_values>\");  // Second set of index values for fall power
                    values(\"<values>\");  // Fall power values
                }}
                rise_power (\"<rise_power_group>\") {{
                    index_1(\"<index_values>\");  // Index values for rise power
                    index_2(\"<index_values>\");  // Second set of index values for rise power
                    values(\"<values>\");  // Rise power values
                }}
            }}
            // Repeat internal_power blocks as needed for different conditions
            
            // Maximum capacitance of the output pin
            max_capacitance : <max_capacitance_value>;  // The maximum capacitance the pin can drive
            // Maximum transition time of the output pin
            max_transition : <max_transition_value>;   // The maximum transition time for the cell

            // Power down function
            power_down_function : \"<power_down_function>\";  // Function that determines when the cell powers down

            // Related ground and power pins
            related_ground_pin : \"<related_ground_pin>\";  // The related ground pin
            related_power_pin : \"<related_power_pin>\";  // The related power pin

            // Timing information for the cell
            timing () {{
                // Fall Propagation Delay
                cell_fall (\"<timing_group>\") {{ 
                    index_1(\"<index_values>\");  // Index values for cell fall timing
                    index_2(\"<index_values>\");  // Second set of index values for cell fall timing
                    values(\"<values>\");  // Fall timing values
                }}

                // Rise Propagation Delay
                cell_rise (\"<timing_group>\") {{
                    index_1(\"<index_values>\");  // Index values for cell rise timing
                    index_2(\"<index_values>\");  // Second set of index values for cell rise timing
                    values(\"<values>\");  // Rise timing values
                }}

                // Output fall transition time 
                fall_transition (\"<timing_group>\") {{
                    index_1(\"<index_values>\");  // Index values for fall transition timing
                    index_2(\"<index_values>\");  // Second set of index values for fall transition timing
                    values(\"<values>\");  // Fall transition values
                }}
                
                // Output rise transition time 
                rise_transition (\"<timing_group>\") {{
                    index_1(\"<index_values>\");  // Index values for rise transition timing
                    index_2(\"<index_values>\");  // Second set of index values for rise transition timing
                    values(\"<values>\");  // Rise transition values
                }}
                related_pin : \"<related_pin>\";  // The pin related to this timing information
                timing_sense : \"<timing_sense>\";  // The timing sense (e.g., positive_unate, negative_unate)
                timing_type : \"<timing_type>\";  // The timing type (e.g., combinational, sequential)
            }}
            // Repeat timing blocks as needed for different timing groups
        }}
    }}
"""

lef_template = """
MACRO <macro_name>  // Macro name
    CLASS CORE ;  // Class of the cell
    FOREIGN <foreign_macro_name> ;  // Foreign macro name, usually same as macro name
    ORIGIN <origin_x> <origin_y> ;  // Origin of the cell in the layout
    SIZE <size_x> BY <size_y> ;  // Size of the cell, size_x is width, size_y is height
    SYMMETRY X Y R90 ;  // Symmetry of the cell, e.g., X, Y, and 90-degree rotation
    SITE <site_name> ;  // Site type for the cell

    // Pin definitions
    PIN <pin_name>
        DIRECTION <input_or_output> ;  // Direction of the pin
        USE <use_type> ;  // Use type of the pin (e.g., SIGNAL, POWER, GROUND)
        ANTENNAGATEAREA <antenna_gate_area_value> ;  // Antenna gate area for the pin 
        PORT
        LAYER <layer_name> ;  // Layer information for the port
            RECT <rect_x1> <rect_y1> <rect_x2> <rect_y2> ;  // Rectangle coordinates defining the port area
        END
    END <pin_name>
    // Repeat PIN blocks as needed for each pin

    // Example for a pin with different properties
    PIN <pin_name>
        DIRECTION <input_or_output> ;
        USE <use_type> ;
        ANTENNADIFFAREA <antenna_diff_area_value> ;  // Antenna diff area for the pin 
        PORT
        LAYER <layer_name> ;
            // Pin Rectangles
            RECT <rect_x1> <rect_y1> <rect_x2> <rect_y2> ;
            RECT <rect_x3> <rect_y3> <rect_x4> <rect_y4> ;  // Additional rectangles if needed
        END
    END <pin_name>

    // OBS section for obstructed areas in the cell
    OBS
        LAYER <layer_name> ;  // Layer information for the obstruction
        RECT <rect_x1> <rect_y1> <rect_x2> <rect_y2> ;  // Rectangle coordinates defining the obstructed area
        // Repeat RECT lines as needed for different obstructed areas
        LAYER <additional_layer_name> ;
        RECT <rect_x1> <rect_y1> <rect_x2> <rect_y2> ;
        // Repeat RECT lines as needed for different obstructed areas on additional layers
    END
END <macro_name>

"""

tlef_template = """
LAYER <layer_name>
    TYPE <type>;  // Layer type (e.g., ROUTING, CUT, MASTERSLICE)
    DIRECTION <direction>;  // Direction of the routing layer (e.g., HORIZONTAL, VERTICAL)

    PITCH <pitch_value>;  // Pitch of the routing layer
    OFFSET <offset_value>;  // Offset of the routing layer

    WIDTH <width_value>;  // Width of the routing layer
    // Optional spacing rules
    // SPACING <spacing_value>;  // Minimum spacing rule for the layer
    // SPACING <spacing_value> RANGE <range_start> <range_end>;  // Spacing rule with range
    SPACINGTABLE
        PARALLELRUNLENGTH <parallel_run_length_value>  // Parallel run length
        WIDTH <width_1> <spacing_1>  // Spacing table width and spacing values
        WIDTH <width_2> <spacing_2>;  // Additional width and spacing values
    AREA <area_value>;  // Minimum area rule for the layer
    THICKNESS <thickness_value>;  // Thickness of the routing layer
    MINENCLOSEDAREA <min_enclosed_area_value>;  // Minimum enclosed area rule

    // Antenna rules
    ANTENNAMODEL <antenna_model_type>;  // Antenna model type
    ANTENNADIFFSIDEAREARATIO PWL ( ( <point_1_x> <point_1_y> ) ( <point_2_x> <point_2_y> ) ... );  // Piecewise linear (PWL) antenna diff side area ratio

    // Electrical properties
    EDGECAPACITANCE <edge_capacitance_value>;  // Edge capacitance of the layer
    CAPACITANCE CPERSQDIST <capacitance_per_square_distance_value>;  // Capacitance per square distance
    DCCURRENTDENSITY AVERAGE <dc_current_density_value>;  // DC current density (average)
    ACCURRENTDENSITY RMS <ac_current_density_value>;  // AC current density (RMS)
    MAXIMUMDENSITY <maximum_density_value>;  // Maximum density rule
    DENSITYCHECKWINDOW <density_check_window_x> <density_check_window_y>;  // Density check window size
    DENSITYCHECKSTEP <density_check_step_value>;  // Density check step size

    RESISTANCE RPERSQ <resistance_per_square_value>;  // Resistance per square
END <layer_name>
"""
