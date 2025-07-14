import odb
import os

# Paths to the .odb files for different design stages
odb_files = {
    "floorplan": "/home/manar/PDQ/designs/usbc-core/floorplan/usb_cdc_core.odb",
    "placement": "/home/manar/PDQ/designs/usbc-core/placement/usb_cdc_core.odb",
    "cts": "/home/manar/PDQ/designs/usbc-core/cts/usb_cdc_core.odb",
    "routing": "/home/manar/PDQ/designs/usbc-core/routing/usb_cdc_core.odb",
}

# Function to count buffer cells in a given .odb file
def count_buffers(odb_file):
    if not os.path.exists(odb_file):
        print(f"Error: Database file {odb_file} not found.")
        return None

    # Create a new database instance
    db = odb.dbDatabase.create()

    try:
        # Load the ODB file
        odb.read_db(db, odb_file)

        # Get the chip object
        chip = db.getChip()
        if not chip:
            print(f"Error: Chip object not found in {odb_file}.")
            return None

        # Get the block object
        block = chip.getBlock()
        if not block:
            print(f"Error: Block object not found in {odb_file}.")
            return None

        # Count buffer cells
        buffer_count = 0
        for inst in block.getInsts():
            master = inst.getMaster()
            if not master:
                continue

            # Check if the cell is a buffer based on naming convention
            cell_name = master.getName().upper()
            if "BUF" in cell_name:  # Adjust naming convention as needed
                buffer_count += 1

        return buffer_count

    finally:
        # Destroy the database instance explicitly
        odb.dbDatabase.destroy(db)

# Process each design stage
buffer_counts = {}
for stage, odb_file in odb_files.items():
    buffer_counts[stage] = count_buffers(odb_file)

# Report the results
for stage, count in buffer_counts.items():
    if count is not None:
        print(f"{stage.capitalize()}: {count}")
    else:
        print(f"{stage.capitalize()}: Error processing this stage")
