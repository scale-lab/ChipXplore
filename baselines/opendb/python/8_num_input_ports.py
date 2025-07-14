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

# Count the number of input ports
input_port_count = sum(1 for port in ports if port.getIoType() == "INPUT")

# Report the number of input ports
print(input_port_count)
