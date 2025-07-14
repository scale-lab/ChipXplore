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

# Get database units per micron
db_units_per_micron = db.getTech().getDbUnitsPerMicron()

# Get the die area
die_area = block.getDieArea()

# Extract coordinates
llx, lly = die_area.ll()  # Lower-left corner (x, y)
urx, ury = die_area.ur()  # Upper-right corner (x, y)

# Compute dimensions in microns
width_microns = (urx - llx) / db_units_per_micron
height_microns = (ury - lly) / db_units_per_micron

# Compute die area in square microns
area_microns = width_microns * height_microns

print(f"{area_microns:.2f} square microns")
