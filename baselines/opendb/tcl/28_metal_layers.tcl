# Define the path to the database file
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
set pdk_path "/home/manar/.volare/sky130A/libs.ref"
set scl_variant "sky130_fd_sc_hd"

set lib_path [file join $pdk_path $scl_variant "lib"]
set techlef_path [file join $pdk_path $scl_variant "techlef"]
set lef_path [file join $pdk_path $scl_variant "lef"]

# Read technology and cell LEF files
set tech_files [glob -directory $techlef_path *.tlef]
foreach tech_file $tech_files {
    if {[string first "nom" $tech_file] != -1} {
        read_lef $tech_file
    }
}
# Check if the database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}

# Load the database
read_db $odb_file
set db [ord::get_db]

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

# Use a dictionary to emulate a set for unique metal layers
array set unique_layers {}

# Iterate over all nets in the block
foreach net [$block getNets] {
    set wire [$net getWire]
    # Safely get the wire for the net
    if {[catch {set wire [$net getWire]}] || [string equal $wire ""] || $wire == "NULL"} {
        continue
    }

    # Safely initialize the wire decoder
    set wire_iter [odb::dbWireDecoder]
    if {[catch {$wire_iter begin $wire}]} {
        continue
    }

    while {1} {
        set current_opcode [$wire_iter peek]
        puts $current_opcode
        if {$current_opcode == 12} {
            break
        } else {
            set layer [$wire_iter getLayer]         
            # Ensure the layer object is valid
            if {[catch {set name [$layer getName]}] || [string equal $name ""]} {
                $wire_iter next
                continue
            }

            # Add to the set by using the layer name as a key in the dictionary
            set unique_layers($name) 1
        }
        $wire_iter next
    }
}

# Extract keys from the dictionary to get the unique layers
set layer_list [array names unique_layers]

# Report the number of unique metal layers
puts "Number of Unique Metal Layers Used: [llength $layer_list]"
puts "Unique Layers: [lsort $layer_list]"
