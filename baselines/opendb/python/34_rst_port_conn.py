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

# Find the net connected to the rst_i port
rst_i_net = None
for port in block.getBTerms():
    if port.getName() == "rst_i":
        rst_i_net = port.getNet()
        break

if not rst_i_net:
    print("Error: rst_i port not found or not connected to any net.")
    exit(1)

# Find the cells connected to the rst_i net
connected_cells = set()
for iterm in rst_i_net.getITerms():
    inst = iterm.getInst()
    if inst:
        connected_cells.add(inst.getName())

# Report the connected cells
if connected_cells:
    print(f"Cells connected to rst_i port: {', '.join(connected_cells)}")
else:
    print("No cells are connected to the rst_i port.")
