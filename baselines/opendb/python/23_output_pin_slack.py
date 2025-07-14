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

cell_name = None
largest_slack = 0 

for inst in block.getInsts():
    inst_ITerms = inst.getITerms()

    for ITerm in inst_ITerms:
        if ITerm.isOutputSignal():
            slack = min(timing.getPinSlack(ITerm, timing.Fall, timing.Max), timing.getPinSlack(ITerm, timing.Rise, timing.Max))

            if slack > largest_slack: 
                largest_slack = slack
                cell_name = inst.getName()

print(f"Cell with the largest output pin slack: {cell_name}")

