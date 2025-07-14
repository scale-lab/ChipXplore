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

# Initialize buffer cell count
buffer_count = 0

# Iterate over all instances in the block
for inst in block.getInsts():
    master = inst.getMaster()
    if not master:
        continue

    # Check if the cell is a buffer based on its name (adjust naming convention as necessary)
    cell_name = master.getName()
    if "INV" in cell_name.upper():  # Case-insensitive check for "BUF"
        buffer_count += 1

# Report the buffer cell count
print(buffer_count)
