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

# Identify clock nets
set clock_nets {}
set nets [$block getNets]
foreach net $nets {
    set net_name [string toupper [$net getName]]
    if {[string first "CLK" $net_name] >= 0} {
        lappend clock_nets $net
    }
}

# Collect cells connected to clock nets
set counter 0
foreach net $clock_nets {
    set iterms [$net getITerms]
    foreach term $iterms {
        set inst [$term getInst]
        if {[info exists inst]} {
            set inst_name [$inst getName]
            incr counter
        }
    }
}

# Report the results
puts "Number of Cells in the Clock Tree Network: $counter"
