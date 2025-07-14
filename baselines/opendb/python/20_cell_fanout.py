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

# Initialize variables to track the cell with the largest fanout
max_fanout = 0
largest_fanout_cell = None

# Iterate over all instances in the block
for inst in block.getInsts():
    fanout_count = 0

    # Get the output pins of the instance
    for pin in inst.getITerms():
        net = pin.getNet()
        if pin.getSigType() == "OUTPUT": 
            print(pin.getSigType())
        if net and pin.isOutputSignal():
            # Count the number of cells connected to this net
            fanout_count += len(net.getITerms())

    # Check if this cell has the largest fanout
    if fanout_count > max_fanout:
        max_fanout = fanout_count
        largest_fanout_cell = inst.getName()

# Report the cell with the largest fanout
print(largest_fanout_cell)
