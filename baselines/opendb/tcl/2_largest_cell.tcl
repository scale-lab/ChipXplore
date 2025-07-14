# Define the path to the database file
set odb_file /home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb

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

# Iterate over all instances to find the cell with the largest area
set largest_area 0
set largest_cell_name ""

foreach inst [$block getInsts] {
    set master [$inst getMaster]
    if {$master eq ""} {
        continue
    }

    # Get the cell's bounding box
    set bbox [$inst getBBox]
    if {$bbox eq ""} {
        continue
    }

    # Compute the cell area
    set llx [$bbox xMin]
    set lly [$bbox yMin]
    set urx [$bbox xMax]
    set ury [$bbox yMax]
    set cell_area [expr {($urx - $llx) * ($ury - $lly)}]

    # Update largest cell information
    if {$cell_area > $largest_area} {
        set largest_area $cell_area
        set largest_cell_name [$master getName]
    }
}

# Report the largest cell
if {$largest_cell_name ne ""} {
    puts "Largest Cell: $largest_cell_name"
    puts "Area: $largest_area (in database units squared)"
} else {
    puts "No cells found in the design."
}
