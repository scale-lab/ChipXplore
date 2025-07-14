# Define the path to the database file
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"

# Check if the database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}
# Load the database
read_db $odb_file
set db [::ord::get_db]

# Get the chip object
set chip [$db getChip]
if {![info exists chip]} {
    puts "Error: Chip object not found in the database"
    exit 1
}

# Get the block object
set block [$chip getBlock]
if {![info exists block]} {
    puts "Error: Block object not found in the chip"
    exit 1
}

# Get the boundary terms (ports)
set ports [$block getBTerms]

# Initialize a list for input ports on Metal 3 (met3)
set input_ports_on_met3 {}

# Filter input ports drawn on Metal 3 layer
foreach port $ports {
    if {[$port getIoType] == "INPUT"} {
        # Check for pin shapes and associated layer
        set pins [$port getBPins]
        foreach pin $pins {
            set boxes [$pin getBoxes]
            foreach box $boxes {
                set layer [$box getTechLayer]
                if {[info exists layer] && [$layer getName] == "met3"} {
                    lappend input_ports_on_met3 [$port getName]
                    break
                }
            }
        }
    }
}

# Report input ports on Metal 3 layer
puts "Input Ports on Metal 3 (met3): $input_ports_on_met3"
