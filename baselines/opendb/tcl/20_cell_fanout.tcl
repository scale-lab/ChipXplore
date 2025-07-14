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

# Initialize variables to track the cell with the largest fanout
set max_fanout 0
set largest_fanout_cell ""

# Iterate over all instances in the block
set instances [$block getInsts]
foreach inst $instances {
    set fanout_count 0

    # Get the internal terms (pins) of the instance
    set pins [$inst getITerms]
    foreach pin $pins {
        # Check if the net exists and is valid
        set net [$pin getNet]
        if {$net ne "" && [info exists net] && $net ne {NULL} && [$pin getIoType] eq "OUTPUT"} {
            # Count the number of internal terms connected to this net
            set iterms [$net getITerms]
            if {[info exists iterms]} {
                set fanout_count [expr {$fanout_count + [llength $iterms]}]
            }
        }
    }

    # Check if this cell has the largest fanout
    if {$fanout_count > $max_fanout} {
        set max_fanout $fanout_count
        set largest_fanout_cell [$inst getName]
    }
}

# Report the cell with the largest fanout
if {$largest_fanout_cell ne ""} {
    puts "Cell with the Largest Fanout: $largest_fanout_cell"
    puts "Fanout Count: $max_fanout"
} else {
    puts "No driving cells found in the design."
}
