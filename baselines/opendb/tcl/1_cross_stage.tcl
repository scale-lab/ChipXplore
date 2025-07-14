# Paths to the .odb files for different design stages
set odb_files {
    floorplan "/home/manar/PDQ/designs/usbc-core/floorplan/usb_cdc_core.odb"
    placement "/home/manar/PDQ/designs/usbc-core/placement/usb_cdc_core.odb"
    cts "/home/manar/PDQ/designs/usbc-core/cts/usb_cdc_core.odb"
    routing "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
}

# Function to count buffer cells in a given .odb file
proc count_buffers {odb_file} {
    # Check if the file exists
    if {![file exists $odb_file]} {
        puts "Error: Database file $odb_file not found."
        return -1
    }

    # Disown the current database to reset the state
    set db [::ord::get_db]
    if {$db ne ""} {
        $db clear
    }

    # Load the new database
    read_db $odb_file
    set db [::ord::get_db]

    # Get the chip object
    set chip [$db getChip]
    if {$chip eq ""} {
        puts "Error: Chip object not found in $odb_file."
        return -1
    }

    # Get the block object
    set block [$chip getBlock]
    if {$block eq ""} {
        puts "Error: Block object not found in $odb_file."
        return -1
    }

    # Count buffer cells
    set buffer_count 0
    foreach inst [$block getInsts] {
        set master [$inst getMaster]
        if {$master eq ""} {
            continue
        }

        # Check if the cell is a buffer based on naming convention
        set cell_name [string toupper [$master getName]]
        if {[string match *BUF* $cell_name]} {
            incr buffer_count
        }
    }

    return $buffer_count
}

# Process each design stage
foreach {stage odb_file} $odb_files {
    set buffer_count [count_buffers $odb_file]
    if {$buffer_count >= 0} {
        puts "[string toupper $stage]: $buffer_count buffer cells"
    } else {
        puts "[string toupper $stage]: Error processing this stage"
    }
}
