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

# Initialize buffer cell count
set buffer_count 0

# Iterate over all instances in the block
set instances [$block getInsts]
foreach inst $instances {
    set master [$inst getMaster]
    if {![info exists master]} {
        continue
    }

    # Check if the cell is a buffer based on its name
    set cell_name [$master getName]
    if {[string first "BUF" [string toupper $cell_name]] >= 0} {
        incr buffer_count
    }
}

# Report the buffer cell count
puts "$buffer_count"
