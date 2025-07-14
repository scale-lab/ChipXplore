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

# Identify the clock net
set clock_net ""
set nets [$block getNets]
foreach net $nets {
    if {[$net getSigType] eq "CLOCK"} {
        set clock_net $net
        break
    }
}

if {$clock_net eq ""} {
    puts "Error: No clock net found in the design."
    exit 1
}

# Count the number of cells connected to the clock net
set connected_cells {}
set iterms [$clock_net getITerms]

foreach iterm $iterms {
    set inst [$iterm getInst]
    if {$inst ne ""} {
        lappend connected_cells [$inst getName]
    }
}

# Remove duplicates and count the unique cells
set num_cells [llength $connected_cells]

# Report the results
puts "Number of Cells Connected to the Clock Net: $num_cells"
if {$num_cells > 0} {
    puts "Connected Cells: $connected_cells "
}
