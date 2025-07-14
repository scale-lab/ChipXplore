# Paths
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"

# Initialize the OpenROAD database
puts "Initializing OpenROAD database..."
read_db $odb_file

# Check if the database is loaded
set db [ord::get_db]
set chip [$db getChip]
if {$chip eq ""} {
    puts "Error: Chip object not found in the database"
    exit 1
}

set block [$chip getBlock]
if {$block eq ""} {
    puts "Error: Block object not found in the chip"
    exit 1
}

# Generate the power report
puts "Generating power report..."
set power_report [sta::report_power]

# Debug: Print the raw power report
puts "Raw Power Report:\n$power_report"

# Parse the power report to find the cell with the largest static power
set largest_power 0
set largest_power_cell ""

foreach line [split $power_report \n] {
    # Parse each line to extract cell name and power
    # Adjust parsing logic based on actual report format
    set fields [split $line]
    if {[llength $fields] < 2} {
        continue
    }
    set cell_name [lindex $fields 0]
    set static_power [lindex $fields 1]

    # Update the largest power and corresponding cell
    if {$static_power > $largest_power} {
        set largest_power $static_power
        set largest_power_cell $cell_name
    }
}

# Report the cell with the largest static power
if {$largest_power_cell eq ""} {
    puts "Error: No valid static power data found in the report"
} else {
    puts "Cell with the largest static power: $largest_power_cell ($largest_power)"
}
