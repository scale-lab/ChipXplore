import os
import openroad as ord

from openroad import Tech, Design, Timing

# Define the path to the database file
odb_file = "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb"

tech = Tech()
if not os.path.exists(odb_file):
    print("Error: Database file not found")
    exit(1)

design = Design(tech) 
design.readDb(odb_file)
db = ord.get_db()

dbunits = db.getTech().getDbUnitsPerMicron()

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

# Initialize variables to track the net with the largest routed length
max_length = 0
largest_routed_net = None

# Iterate over all nets in the block
for net in block.getNets():
    # Get the total routed length of the net
    routed_length = design.getNetRoutedLength(net) / dbunits

    # Check if this net has the largest routed length
    if routed_length > max_length:
        max_length = routed_length
        largest_routed_net = net.getName()

# Report the net with the largest routed length
if largest_routed_net:
    print(f"Net with the Largest Routed Length: {largest_routed_net}")
    print(f"Routed Length: {max_length} units")
else:
    print("No routed nets found in the design.")
