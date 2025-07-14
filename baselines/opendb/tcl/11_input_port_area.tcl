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

# Initialize variables to track the largest input port and area
set largest_area 0
set largest_input_port ""

# Find the input port with the largest area, excluding power and ground pins
foreach port $ports {
    if {[$port getIoType] == "INPUT" && ![string match "POWER" [$port getSigType]] && ![string match "GROUND" [$port getSigType]]} {
        # Calculate the total area of the port
        set port_area 0
        set pins [$port getBPins]
        foreach pin $pins {
            set boxes [$pin getBoxes]
            foreach box $boxes {
                set llx [$box xMin]
                set lly [$box yMin]
                set urx [$box xMax]
                set ury [$box yMax]
                set area [expr {($urx - $llx) * ($ury - $lly)}]
                set port_area [expr {$port_area + $area}]
            }
        }
        
        # Check if this port has the largest area
        if {$port_area > $largest_area} {
            set largest_area $port_area
            set largest_input_port [$port getName]
        }
    }
}

# Report the input port with the largest area
if {$largest_input_port ne ""} {
    puts "Largest Input Port: $largest_input_port"
    puts "Area: $largest_area square database units"
} else {
    puts "No input ports found in the design."
}
