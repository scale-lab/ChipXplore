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

# Initialize counter for electrically isolated cells
isolated_cells = 0

# Iterate over all instances in the block
for inst in block.getInsts():
    is_isolated = True

    # Check if any of the instance's pins are connected to a net
    for iterm in inst.getITerms():
        if iterm.getNet():  # If any pin is connected to a net, the cell is not isolated
            is_isolated = False
            break

    # Count the instance if it is isolated
    if is_isolated:
        isolated_cells += 1

# Report the number of isolated cells
print(f"Number of Electrically Isolated Cells: {isolated_cells}")
