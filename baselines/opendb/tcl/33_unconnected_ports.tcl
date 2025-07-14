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
if {$chip eq ""} {
    puts "Error: Chip object not found in the database"
    exit 1
}

# Get the block object
set block [$chip getBlock]
if {$block eq ""} {
    puts "Error: Block object not found in the chip"
    exit 1
}

# Initialize list and counter for unconnected ports
set unconnected_ports []

# Iterate over all ports in the block
set ports [$block getBTerms]

foreach port $ports {
    set net [$port getNet]
    puts $net 
    puts [$net getName]
    if {[string equal $net ""] || [string equal [$net getName] ""]} {
        lappend unconnected_ports [$port getName]
    }
}

# Report the number of unconnected ports
set num_unconnected [llength $unconnected_ports]
puts "Number of Unconnected Ports: $num_unconnected"
if {$num_unconnected > 0} {
    puts "Unconnected Ports: [join $unconnected_ports \", \"]"
}
