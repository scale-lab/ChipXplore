import odb
import os

# Define the path to the database file
odb_file = "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"

# Check if the database file exists
if not os.path.exists(odb_file):
    print("Error: Database file not found")
    exit(1)

# Load the database
db = odb.dbDatabase.create()
odb.read_db(db, odb_file)

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

# Identify the clock net
clock_net = None
for net in block.getNets():
    if net.getSigType() == "CLOCK":  # Signal type check
        clock_net = net
        break

if not clock_net:
    print("Error: No clock net found in the design.")
    exit(1)

# Count the number of cells connected to the clock net
connected_cells = set()
for iterm in clock_net.getITerms():
    inst = iterm.getInst()
    if inst:
        connected_cells.add(inst.getName())

# Report the results
print(f"Number of Cells Connected to the Clock Net: {len(connected_cells)}")
