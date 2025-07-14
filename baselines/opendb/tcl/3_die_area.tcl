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

# Get database units per micron
set tech [$db getTech]
set db_units_per_micron [$tech getDbUnitsPerMicron]

# Get the die area
set die_area [$block getDieArea]

# Extract coordinates
set llx [lindex [$die_area ll] 0] 
set lly [lindex [$die_area ll] 1]  
set urx [lindex [$die_area ur] 0] 
set ury [lindex [$die_area ur] 1]  

# Compute dimensions in microns
set width_microns [expr {($urx - $llx) / $db_units_per_micron}]
set height_microns [expr {($ury - $lly) / $db_units_per_micron}]

# Compute die area in square microns
set area_microns [expr {$width_microns * $height_microns}]

puts "$area_microns square microns"
