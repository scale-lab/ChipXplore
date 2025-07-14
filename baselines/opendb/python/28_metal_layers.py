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

# Set to store unique metal layers
unique_layers = set()

# Iterate over all nets in the block
for net in block.getNets():
    wire = net.getWire()
    if not wire:
        continue

    # Traverse the wire segments of the net
    wire_iter = odb.dbWireDecoder()
    wire_iter.begin(wire)
    
    while True: 
        current_opcode = wire_iter.peek()
        if current_opcode in [odb.dbWireDecoder.PATH, odb.dbWireDecoder.SHORT, odb.dbWireDecoder.VWIRE]:
            layer = wire_iter.getLayer()
            if layer:
                unique_layers.add(layer.getName())

        if current_opcode == odb.dbWireDecoder.END_DECODE:
          break
        wire_iter.next()

# Report the number of unique metal layers
print(f"Number of Unique Metal Layers Used: {len(unique_layers)}")
print(f"Unique Layers: {sorted(unique_layers)}")
