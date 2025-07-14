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

# Initialize variables to track the net with the largest fanout
set max_fanout 0
set largest_fanout_net ""

# Iterate over all nets in the block
set nets [$block getNets]
foreach net $nets {
    # Exclude power and ground nets by checking signal type
    set sig_type [$net getSigType]
    if {$sig_type eq "POWER" || $sig_type eq "GROUND"} {
        continue
    }

    # Get the fanout count of the net
    set iterms [$net getITerms]
    set fanout_count [llength $iterms]

    # Check if this net has the largest fanout
    if {$fanout_count > $max_fanout} {
        set max_fanout $fanout_count
        set largest_fanout_net [$net getName]
    }
}

# Report the net with the largest fanout
if {$largest_fanout_net ne ""} {
    puts "Net with the Largest Fanout (excluding power and ground): $largest_fanout_net"
    puts "Fanout Count: $max_fanout"
} else {
    puts "No eligible nets found in the design."
}
