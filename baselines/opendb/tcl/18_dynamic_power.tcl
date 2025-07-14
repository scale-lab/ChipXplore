# Set paths
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
set pdk_path "/home/manar/.volare/sky130A/libs.ref"
set scl_variant "sky130_fd_sc_hd"

set lib_path [file join $pdk_path $scl_variant "lib"]
set techlef_path [file join $pdk_path $scl_variant "techlef"]
set lef_path [file join $pdk_path $scl_variant "lef"]

# Read liberty files
set liberty_files [glob -directory $lib_path *.lib]
foreach liberty $liberty_files {
    if {[string first "ccsnoise" $liberty] == -1} {
        read_liberty $liberty
    }
}

# Read technology and cell LEF files
set tech_files [glob -directory $techlef_path *.tlef]
foreach tech_file $tech_files {
    if {[string first "nom" $tech_file] != -1} {
        read_lef $tech_file
    }
}

set lef_files [glob -directory $lef_path *.lef]
foreach lef $lef_files {
    read_lef $lef
}

# Check if database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}

# Read design database
read_db $odb_file

# Initialize variables for tracking largest power
set largest_power 0
set largest_power_cell ""

# Get the current block
set block [ord::get_db_block]
if {$block == ""} {
    puts "Error: Block object not found"
    exit 1
}

# Set default activity rates for power analysis
# set_switching_activity -global -activity 0.2 -duty 0.5

# Iterate through all instances
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    if {$master == ""} {
        continue
    }
    
    # Get instance name
    set inst_name [$inst getName]
    
    # Get the total power for this instance using report_power
    set power_info [report_power -instances $inst_name]
    
    # Extract power value from the report
    # The exact regexp pattern might need adjustment based on the actual output format
    if {[regexp {total\s+power\s+=\s+(\d+\.?\d*)} $power_info match power_value]} {
        if {$power_value > $largest_power} {
            set largest_power $power_value
            set largest_power_cell $inst_name
        }
    }
}

# Report results
if {$largest_power_cell != ""} {
    puts "Cell with the Largest Power: $largest_power_cell"
    puts "Power: $largest_power units"
} else {
    puts "No power information available in the design."
}