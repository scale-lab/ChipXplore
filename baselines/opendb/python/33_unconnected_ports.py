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

# Count the number of unconnected ports
unconnected_ports = []
for port in block.getBTerms():
    net = port.getNet()  # Get the net associated with the port
    if not net:  # Check if the port is not connected to any net
        unconnected_ports.append(port.getName())

    connected_to_cells = False
    for iterm in net.getITerms():
        if iterm.getInst():  # If the net is connected to any instance
            connected_to_cells = True
            break

    if not connected_to_cells:
        unconnected_ports.append(port.getName())

# Report the number of unconnected ports
print(f"Number of Unconnected Ports: {len(unconnected_ports)}")
if unconnected_ports:
    print(f"Unconnected Ports: {', '.join(unconnected_ports)}")
