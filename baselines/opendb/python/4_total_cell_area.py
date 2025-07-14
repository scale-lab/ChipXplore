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

# Initialize total area
total_area = 0

# Get database units per micron
db_units_per_micron = db.getTech().getDbUnitsPerMicron()

# Iterate over all instances to calculate the total cell area
for inst in block.getInsts():
    # Get the cell's bounding box
    bbox = inst.getBBox()
    if not bbox:
        continue

    # Compute the cell area
    llx, lly = bbox.xMin(), bbox.yMin()
    urx, ury = bbox.xMax(), bbox.yMax()
    cell_area = (urx - llx) * (ury - lly)

    # Accumulate the total area
    total_area += cell_area

# Convert total area to square microns
total_area_microns = total_area / (db_units_per_micron ** 2)

# Report the total area
print(f"{total_area_microns:.2f} square microns")
