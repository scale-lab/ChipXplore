
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

# Get the number of nets in the design
set nets [$block getNets]
set net_count [llength $nets]

# Report the number of nets
puts "Number of Nets in the Design: $net_count"
