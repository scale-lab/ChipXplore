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

# Initialize variables to track the net with the largest routed length
set max_length 0
set largest_routed_net ""

# Iterate over all nets in the block
foreach net [$block getNets] {
    # Get wire segments for the net
    set wire_length 0
    set wires [$net getWire]
    
    if {$wires != "NULL"} {
        # Get the total length of the wire
        set wire_length [$wires getLength]
    }
    
    # Convert to microns
    set routed_length [expr {double($wire_length) / $dbunits}]
    
    # Check if this net has the largest routed length
    if {$routed_length > $max_length} {
        set max_length $routed_length
        set largest_routed_net [$net getName]
    }
}

# Report the net with the largest routed length
if {$largest_routed_net != ""} {
    puts "Net with the Largest Routed Length: $largest_routed_net"
    puts "Routed Length: $max_length microns"
} else {
    puts "No routed nets found in the design."
}