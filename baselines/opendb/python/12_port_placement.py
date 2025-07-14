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

# Get the die area to identify the bottom side
die_area = block.getDieArea()
llx, lly = die_area.ll()  # Lower-left corner (x, y)
urx, ury = die_area.ur()  # Upper-right corner (x, y)

# Get the ports
ports = block.getBTerms()

# Find ports placed on the bottom side of the design
bottom_ports = []
for port in ports:
    for pin in port.getBPins():
        for box in pin.getBoxes():
            llx_box, lly_box = box.xMin(), box.yMin()
            urx_box, ury_box = box.xMax(), box.yMax()

            # Check if the port is on the bottom side (y-coordinate matches the die's bottom edge)
            if lly_box == lly :
                bottom_ports.append(port.getName())
                break

# Report the bottom-side ports
print(bottom_ports)
