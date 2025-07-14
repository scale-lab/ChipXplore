# OpenROAD script to analyze net capacitances
# Set paths
set odb_file "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
set pdk_path "/home/manar/.volare/sky130A/libs.ref"
set scl_variant "sky130_fd_sc_hd"

set lib_path [file join $pdk_path $scl_variant "lib"]
set techlef_path [file join $pdk_path $scl_variant "techlef"]
set lef_path [file join $pdk_path $scl_variant "lef"]

# Create lists of files
set liberty_files [glob -directory $lib_path -nocomplain "*"]
set tech_files [glob -directory $techlef_path -nocomplain "*nom*"]
set lef_files [glob -directory $lef_path -nocomplain "*"]

# Filter out ccsnoise files from liberty files
set liberty_files [lsearch -all -inline -not $liberty_files "*ccsnoise*"]

# Check if database file exists
if {![file exists $odb_file]} {
    puts "Error: Database file not found"
    exit 1
}

# Read liberty files
foreach liberty $liberty_files {
    read_liberty $liberty
}

# Read technology and cell LEF files
foreach tech_file $tech_files {
    read_lef $tech_file
}

foreach lef $lef_files {
    read_lef $lef
}

# Read design
read_db $odb_file

# Initialize OpenROAD objects
set block [[[ord::get_db] getChip] getBlock]
if {$block == "NULL"} {
    puts "Error: Block object not found in the database"
    exit 1
}

# Initialize variables for tracking maximum capacitance
set max_capacitance 0
set largest_cap_net ""

# Get all nets
set nets [$block getNets]

# Iterate through all nets
foreach net $nets {
    set net_name [$net getName]
    # Get net capacitance using db API
    set total_capacitance [$net getTotalCapacitance]
    
    puts "$net_name: $total_capacitance"
    
    # Compare and store maximum
    if {$total_capacitance > $max_capacitance} {
        set max_capacitance $total_capacitance
        set largest_cap_net $net_name
    }
}

# Report results
puts "\nResults:"
puts "Net with largest capacitance: $largest_cap_net"
puts "Total Capacitance: $max_capacitance"