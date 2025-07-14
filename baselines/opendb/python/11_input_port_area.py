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

# Get the boundary terms (ports)
ports = block.getBTerms()

# Find the input port with the largest area, excluding power and ground pins
largest_area = 0
largest_input_port = None

for port in ports:
    if port.getIoType() == "INPUT" and port.getSigType() not in ["POWER", "GROUND"]:
        # Calculate the total area of the port
        port_area = 0
        for pin in port.getBPins():
            for box in pin.getBoxes():
                llx, lly = box.xMin(), box.yMin()  # Lower-left corner
                urx, ury = box.xMax(), box.yMax()  # Upper-right corner
                port_area += (urx - llx) * (ury - lly)
        
        # Check if this port has the largest area
        if port_area > largest_area:
            largest_area = port_area
            largest_input_port = port.getName()

# Report the input port with the largest area
print(largest_input_port)

