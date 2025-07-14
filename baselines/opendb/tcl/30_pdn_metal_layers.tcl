# Define the path to the database file
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"

# Check if the database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}

# Load the database
read_db $odb_file
set db [ord::get_db]

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

# Use a dictionary to store unique metal layers
array set unique_layers {}

# Iterate over all nets in the block
foreach net [$block getNets] {
    # Check if the net is a special net
    if {[$net isSpecial]} {
        # Get the special wires for the net
        foreach swire [$net getSWires] {
            # Iterate over the bounding boxes (wires) in the special wire
            foreach box [$swire getWires] {
                set layer [$box getTechLayer]
                # Ensure the layer object is valid
                if {[catch {set name [$layer getName]}] || [string equal $name ""]} {
                    continue
                }
                # Add the layer name to the dictionary
                set unique_layers($name) 1
            }
        }
    }
}

# Extract keys from the dictionary to get the unique layers
set layer_list [array names unique_layers]

# Report the number of unique metal layers
puts "Number of Unique Metal Layers Used: [llength $layer_list]"
puts "Unique Layers: [lsort $layer_list]"
