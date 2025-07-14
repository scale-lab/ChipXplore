import os 
import csv
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine


def delete_database(db_file):
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Database file {db_file} deleted.")
    else:
        print(f"The file does not exist {db_file}.")

def create_views(source, db, variant, corner=None, condition_id=None):
    if source == 'lib':
        create_vritaul_lib_tables(db, variant, condition_id)
    elif source == 'lef':
        create_vritaul_lef_tables(db, variant)
    elif source == 'techlef':
        create_vritaul_tlef_tables(db, variant, corner)
    else:
        raise Exception(f"Invalid Source {source}")
    

def get_variant_prefix(variant):
    if variant == 'HighSpeed':
        return 'sky130_hd_sc_hs'
    elif variant == 'HighDensityLowLeakage':
        return 'sky130_fd_sc_hdll'
    elif variant == 'HighDensity':
        return 'sky130_fd_sc_hd'
    elif variant == 'MediumSpeed': 
        return 'sky130_fd_sc_ms'
    elif variant == 'LowSpeed':
        return 'sky130_fd_sc_ls'
    else: 
        raise Exception(f"Invalid Library Variant {variant}")


def import_csv_to_sql(conn, csv_file, table_name, columns):
    """Import CSV data into a SQL table."""
    cursor = conn.cursor()
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        cursor.executemany(f'INSERT INTO {table_name} ({columns}) VALUES ({", ".join(["?" for _ in columns.split(",")])})', reader)
    conn.commit()



def write_to_csv(file_path, rows):
    """Write data to a CSV file."""
    with open(file_path, mode='a+', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def write_to_csv_header(file_path, headers):
    """Write data to a CSV file."""
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def create_vritaul_lef_tables(db, variant): 
    variant = get_variant_prefix(variant)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredMacros AS
    SELECT * 
    FROM Macros
    WHERE CellVariant = '{variant}';
    """)
    
    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredPins AS
    SELECT * 
    FROM Pins
    WHERE CellVariant = '{variant}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredPinPorts AS
    SELECT * 
    FROM PinPorts
    WHERE CellVariant = '{variant}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredPinPortRectangles AS
    SELECT * 
    FROM PinPortRectangles
    WHERE CellVariant = '{variant}';
    """)
    
    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredObstructions AS
    SELECT * 
    FROM Obstructions
    WHERE CellVariant = '{variant}';
    """)
    
    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredObstructionRectangles AS
    SELECT * 
    FROM ObstructionRectangles
    WHERE CellVariant = '{variant}';
    """)
    

def create_vritaul_tlef_tables(db, variant, corner):
    variant = get_variant_prefix(variant)

    # Create the views
    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredRoutingLayers AS
    SELECT * 
    FROM RoutingLayers
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredAntennaDiffSideAreaRatios AS
    SELECT * 
    FROM AntennaDiffSideAreaRatios
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredCutLayers AS
    SELECT * 
    FROM CutLayers
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredAntennaDiffAreaRatios AS
    SELECT * 
    FROM AntennaDiffAreaRatios
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredVias AS
    SELECT * 
    FROM Vias
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredViaLayers AS
    SELECT * 
    FROM ViaLayers
    WHERE CellVariant = '{variant}' AND Corner = '{corner}';
    """)



def create_vritaul_lib_tables(db, variant, condition_id):
    """ Creates virtual tables to use based on the selected cell variant and operating conditions
    """
    variant = get_variant_prefix(variant)
    # Create the views
    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredOperatingConditions AS
    SELECT * 
    FROM OperatingConditions
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredCells AS
    SELECT * 
    FROM Cells
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredInputPins AS
    SELECT * 
    FROM InputPins
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredOutputPins AS
    SELECT * 
    FROM OutputPins
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredInputPinInternalPowers AS
    SELECT * 
    FROM InputPinInternalPowers
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredTimingTables AS
    SELECT * 
    FROM TimingTables
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)

    db.run(f"""
    CREATE VIEW IF NOT EXISTS FilteredTimingTableValues AS
    SELECT * 
    FROM TimingTableValues
    WHERE CellVariant = '{variant}' AND Condition_ID = {condition_id};
    """)


