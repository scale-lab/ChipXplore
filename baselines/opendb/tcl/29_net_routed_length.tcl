# OpenROAD script to analyze net lengths
# Define paths
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
set pdk_path "/home/manar/.volare/sky130A/libs.ref"
set scl_variant "sky130_fd_sc_hd"

set lib_path [file join $pdk_path $scl_variant "lib"]
set techlef_path [file join $pdk_path $scl_variant "techlef"]
set lef_path [file join $pdk_path $scl_variant "lef"]

# Check if database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}

# Read design
read_db $odb_file

# Get database objects
set db [ord::get_db]
set tech [$db getTech]
set dbunits [$tech getDbUnitsPerMicron]

# Get the chip object
set chip [$db getChip]
if {$chip == "NULL"} {
    puts "Error: Chip object not found in the database"
    exit 1
}

# Get the block object
set block [$chip getBlock]
if {$block == "NULL"} {
    puts "Error: Block object not found in the chip"
    exit 1
}

# Initialize list to store nets with length > 10
set long_nets {}

# Iterate over all nets in the block
foreach net [$block getNets] {
    # Get wire length
    set wire [$net getWire]
    if {$wire != "NULL"} {
        set wire_length [$wire getLength]
        set routed_length [expr {double($wire_length) / $dbunits}]
        
        # Check if length > 10
        if {$routed_length > 10} {
            lappend long_nets [$net getName]
        }
    }
}

# Print the count of nets with length > 10
puts [llength $long_nets]