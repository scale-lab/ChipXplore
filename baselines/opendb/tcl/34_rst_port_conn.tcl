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

# Find the net connected to the rst_i port
set rst_i_net ""
set ports [$block getBTerms]
foreach port $ports {
    if {[$port getName] eq "rst_i"} {
        set rst_i_net [$port getNet]
        break
    }
}

if {$rst_i_net eq ""} {
    puts "Error: rst_i port not found or not connected to any net."
    exit 1
}

# Find the cells connected to the rst_i net
set connected_cells {}
set iterms [$rst_i_net getITerms]
foreach iterm $iterms {
    set inst [$iterm getInst]
    if {$inst ne ""} {
        lappend connected_cells [$inst getName]
    }
}

# Report the connected cells
if {[llength $connected_cells] > 0} {
    puts "Cells connected to rst_i port:  $connected_cells"
} else {
    puts "No cells are connected to the rst_i port."
}
