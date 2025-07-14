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

timing = Timing(design)

corners = timing.getCorners()
if not corners:
    print("Error: No timing corners available")
    exit(1)

corner = corners[0]  

db = ord.get_db()

chip = db.getChip()
if not chip:
    print("Error: Chip object not found in the database")
    exit(1)

block = chip.getBlock()
if not block:
    print("Error: Block object not found in the chip")
    exit(1)

# Initialize variables to track the cell with the largest dynamic power
largest_power = 0
largest_power_cell = None

# Iterate over all instances in the block
for inst in block.getInsts():
    master = inst.getMaster()
    if not master:
        continue

    cell_dynamic_power = timing.dynamicPower(inst, corner)

    if cell_dynamic_power > largest_power:
        largest_power = cell_dynamic_power
        largest_power_cell = inst.getName()

# Report the cell with the largest dynamic power
print(largest_power_cell)
