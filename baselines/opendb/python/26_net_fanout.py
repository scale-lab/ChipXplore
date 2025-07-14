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

# Initialize variables to track the net with the largest fanout
max_fanout = 0
largest_fanout_net = None

# Iterate over all nets in the block
for net in block.getNets():
    # Exclude power and ground nets by checking signal type
    if net.getSigType() in ["POWER", "GROUND"]:
        continue

    # Get the fanout count of the net
    fanout_count = len(net.getITerms())  # Count the number of connected internal terms

    # Check if this net has the largest fanout
    if fanout_count > max_fanout:
        max_fanout = fanout_count
        largest_fanout_net = net.getName()

# Report the net with the largest fanout
if largest_fanout_net:
    print(f"Net with the Largest Fanout (excluding power and ground): {largest_fanout_net}")
    print(f"Fanout Count: {max_fanout}")
else:
    print("No eligible nets found in the design.")
