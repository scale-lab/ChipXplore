import odb
import os
import openroad as ord
from openroad import Tech, Design, Timing

# Define the path to the database file
odb_file = "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"
pdk_path = '/home/manar/.volare/sky130A/libs.ref'

scl_variant = 'sky130_fd_sc_hd'
lib_path = os.path.join(pdk_path, scl_variant, 'lib')

liberty_files = [os.path.join(lib_path, file) for file in os.listdir(lib_path) if 'tt_025C_1v80' in file ]

tech = Tech()
for liberty in liberty_files:  
    tech.readLiberty(liberty)


if not os.path.exists(odb_file):
    print("Error: Database file not found")
    exit(1)


design = Design(tech) 
design.readDb(odb_file)

db = ord.get_db()

timing = Timing(design)

corners = timing.getCorners()
corner = corners[0]  

# Get the chip object
chip = db.getChip()
if not chip:
    print("Error: Chip object not found in the database")
    exit(1)

# Get the block object
block = chip.getBlock()
if not block:
    print("Error: Block object not found in the chip")
    exit(1)

# Initialize variables to track the net with the largest capacitance
max_capacitance = 0
largest_cap_net = None

# Iterate over all nets in the block
for net in block.getNets():
    # Get the total capacitance of the net
    total_capacitance = timing.getNetCap(net, corner, timing.Max)
    # Check if this net has the largest capacitance
    if total_capacitance > max_capacitance:
        max_capacitance = total_capacitance
        largest_cap_net = net.getName()

# Report the net with the largest total capacitance
print(f"Net: {largest_cap_net}")
print(f"Total Capacitance: {max_capacitance} units")
