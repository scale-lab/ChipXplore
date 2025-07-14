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

# Initialize counter for electrically isolated cells
set isolated_cells 0

# Iterate over all instances in the block
set instances [$block getInsts]
foreach inst $instances {
    set is_isolated 1  ;# Assume the cell is isolated

    # Check if any of the instance's pins are connected to a net
    set iterms [$inst getITerms]
    foreach iterm $iterms {
        set net [$iterm getNet]
        if {$net ne ""} {
            set is_isolated 0
            break
        }
    }

    # Count the instance if it is isolated
    if {$is_isolated} {
        incr isolated_cells
    }
}

# Report the number of isolated cells
puts "Number of Electrically Isolated Cells: $isolated_cells"
