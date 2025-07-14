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

# Initialize counters
total_cells = 0
physical_only_cells = 0

# Iterate over all instances in the block
for inst in block.getInsts():
    master = inst.getMaster()
    if not master:
        continue

    total_cells += 1  # Count all cells

    # Check if the cell is physical-only (e.g., filler, decap, tap)
    # Assuming physical-only cells contain "FILL", "TAP", or "DECAP" in their name
    cell_name = master.getName().upper()  # Case-insensitive check
    if "FILL" in cell_name or "TAP" in cell_name or "DECAP" in cell_name:
        physical_only_cells += 1

# Calculate the percentage of physical-only cells
if total_cells > 0:
    physical_only_percentage = (physical_only_cells / total_cells) * 100
else:
    physical_only_percentage = 0

# Report the results
print(f"Total Cells: {total_cells}")
print(f"Physical-Only Cells: {physical_only_cells}")
print(f"Percentage: {physical_only_percentage:.2f}%")
