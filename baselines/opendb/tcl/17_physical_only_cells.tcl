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

# Initialize counters
set total_cells 0
set physical_only_cells 0

# Iterate over all instances in the block
set instances [$block getInsts]
foreach inst $instances {
    set master [$inst getMaster]
    if {![info exists master]} {
        continue
    }

    incr total_cells  ;# Count all cells

    # Check if the cell is physical-only (e.g., filler, decap, tap)
    # Assuming physical-only cells contain "FILL", "TAP", or "DECAP" in their name
    set cell_name [string toupper [$master getName]]
    if {[string first "FILL" $cell_name] >= 0 || [string first "TAP" $cell_name] >= 0 || [string first "DECAP" $cell_name] >= 0} {
        incr physical_only_cells
    }
}

# Calculate the percentage of physical-only cells
if {$total_cells > 0} {
    set physical_only_percentage [expr {($physical_only_cells / $total_cells) * 100.0}]
} else {
    set physical_only_percentage 0
}

# Report the results
puts "Total Cells in the Design: $total_cells"
puts "Physical-Only Cells in the Design: $physical_only_cells"
puts "Percentage of Physical-Only Cells: [format %.2f $physical_only_percentage]%"
