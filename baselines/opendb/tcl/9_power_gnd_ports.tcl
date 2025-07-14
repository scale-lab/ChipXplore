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

# Initialize lists for power and ground ports
set power_ports {}
set ground_ports {}

# Filter power and ground ports
foreach port $ports {
    set sig_type [$port getSigType]
    set port_name [$port getName]
    if {$sig_type == "POWER"} {
        lappend power_ports $port_name
    } elseif {$sig_type == "GROUND"} {
        lappend ground_ports $port_name
    }
}

# Report the names of power and ground ports
puts "Power Ports: $power_ports"
puts "Ground Ports: $ground_ports"
