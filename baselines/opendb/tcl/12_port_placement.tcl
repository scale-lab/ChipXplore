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

# Get the die area to identify the bottom side
set die_area [$block getDieArea]
set llx [$die_area xMin]
set lly [$die_area yMin]
set urx [$die_area xMax]
set ury [$die_area yMax]

# Get the ports
set ports [$block getBTerms]

# Initialize a list for bottom-side ports
set bottom_ports {}

# Find ports placed on the bottom side of the design
foreach port $ports {
    set pins [$port getBPins]
    foreach pin $pins {
        set boxes [$pin getBoxes]
        foreach box $boxes {
            set llx_box [$box xMin]
            set lly_box [$box yMin]
            set urx_box [$box xMax]
            set ury_box [$box yMax]

            # Check if the port is on the bottom side (y-coordinate matches the die's bottom edge)
            if {$lly_box == $lly} {
                lappend bottom_ports [$port getName]
                break
            }
        }
    }
}

# Report the bottom-side ports
puts "$bottom_ports"

