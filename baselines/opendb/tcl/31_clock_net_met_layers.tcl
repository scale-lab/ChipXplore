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

# Use a dictionary to store unique metal layers (acts like a set)
array set unique_layers {}

# Iterate over all nets in the block
foreach net [$block getNets] {
    # Check if the net is a clock net
    if {[$net getSigType] eq "CLOCK"} {
        set wire [$net getWire]
        if {![info exists wire] || $wire == ""} {
            continue
        }

        # Initialize the wire decoder
        set wire_iter [odb::dbWireDecoder]
        if {[catch {$wire_iter begin $wire}]} {
            continue
        }

        while {1} {
            set current_opcode [$wire_iter peek]
            if {$current_opcode == 12} { # END_DECODE
                break
            }

            # Check for valid path, short, or vwire opcodes
            if {($current_opcode == 2 || $current_opcode == 3 || $current_opcode == 4)} {
                set layer [$wire_iter getLayer]
                if {[catch {set name [$layer getName]}] || [string equal $name ""]} {
                    $wire_iter next
                    continue
                }

                # Add to the dictionary (emulating a set)
                set unique_layers($name) 1
            }
            $wire_iter next
        }
    }
}

# Extract keys from the dictionary to get unique layers
set layer_list [array names unique_layers]

# Report the number of unique metal layers
puts "Number of Unique Metal Layers Used: [llength $layer_list]"
puts "Unique Layers: [lsort $layer_list]"
