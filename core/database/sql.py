"""Store the PDK files LEF, LIB, and TechLef Views in one database
"""

import os 
import tqdm
import sqlite3
import argparse 

from config.pdks import get_techlef_corners, get_corner_path, get_scl_corners, get_scl, get_lef_paths, get_lib_paths, get_techlef_paths, get_pdk_path, cell_variant
from config.sky130 import View
from core.database.sql_lib import create_lib_tables, insert_lib_data, get_lib_description, get_lib_foreign_keys, get_lib_table_names
from core.database.sql_lef import create_lef_tables, insert_lef_data, get_lef_description, get_compact_lef_description, get_lef_foreign_keys, get_lef_table_names
from core.database.sql_tlef import create_tlef_tables, insert_tlef_data, get_tlef_description, get_compact_tlef_description, get_tlef_foreign_keys, get_tlef_table_names
from core.parsers.lib.lib_parser import parse_liberty_file
from core.parsers.lef.lef_parser import LefParser
from core.database.sql_lef import drop_cell_library_column
from core.database.sql_tlef import drop_cell_library_corner_columns
from core.database.sql_lib import drop_cell_library_corner_column


def get_desc(source, selected_schema=None, compact=False, partition=False):    

    if source == View.Liberty.value:
        descr = get_lib_description(
            selected_schema=selected_schema,
            partition=partition
        )
    elif source == View.Lef.value:
        descr = get_lef_description(
            selected_schema=selected_schema,
            partition=partition
        )
    elif source ==  View.TechLef.value:
        descr = get_tlef_description(
            selected_schema=selected_schema,
            partition=partition
        )
    elif source is None or source == "":
        descr = get_lib_description(selected_schema, partition=partition) + \
                get_lef_description(selected_schema, partition=partition) + \
                get_tlef_description(selected_schema, partition=partition)
    else: 
        raise Exception(f"Invalid Source {source}")

    return descr 


def get_fk(source, selected_schema=None, partition=False):    
    if source == View.Liberty.value:
        fk_str = get_lib_foreign_keys(selected_schema, partition=partition)
    elif source == View.Lef.value:
        fk_str = get_lef_foreign_keys(selected_schema)
    elif source ==  View.TechLef.value:
        fk_str=  get_tlef_foreign_keys(selected_schema)
    elif source is None or source == "":
        fk_str = get_lib_foreign_keys(selected_schema, partition=partition) + \
                get_lef_foreign_keys(selected_schema) + \
                get_tlef_foreign_keys(selected_schema)
    else:
        raise Exception(f"Invalid Source {source}")

    return fk_str


def get_table_names(source, partition=False): 
    if source == View.Liberty.value:
        return get_lib_table_names(partition=partition)
    elif source == View.Lef.value:
        return get_lef_table_names()
    elif source ==  View.TechLef.value:
        return get_tlef_table_names()
    elif source is None or source == "": 
        return get_lib_table_names(partition=partition) + get_lef_table_names() + get_tlef_table_names()
    else:
        raise Exception(f"Invalid Source {source}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdk_path', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--pdk_name', type=str, help='Path to the sky130 pdk', default='/home/manar/.volare/sky130A/libs.ref')
    parser.add_argument('--output_dir', type=str, help='Path to output director', default='./dbs/sky130')
    parser.add_argument('--csv',  help='Improt database from CSV files (faster)', action='store_true', default=False)
    parser.add_argument('--partition', help='Partition the database by standard cells and operating conditions.', action='store_true', default=False)

    args = parser.parse_args()

    pdk_name = args.pdk_name
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    pdk_name = args.pdk_name
    partition = args.partition

    scl_variants = get_scl(pdk_name)
    techlef_corners = get_techlef_corners(pdk_name)
    scl_corners = get_scl_corners(pdk_name)

    db_conn = dict()

    if not partition:
        conn = sqlite3.connect(":memory:")
        db_conn["single"] = conn
        create_lib_tables(conn)
        create_lef_tables(conn)
        create_tlef_tables(conn)
    else:
        for variant in scl_variants:
            variant_name = cell_variant(pdk_name, [variant.name])[0]

            for tlef_corner in techlef_corners:
                    key = f"{variant_name}_{View.TechLef.value}_{tlef_corner.value}"
                    db_conn[key] = sqlite3.connect(":memory:")  
                    create_tlef_tables(db_conn[key])

            key = f"{variant_name}_{View.Lef.value}"
            db_conn[key] = sqlite3.connect(":memory:")  
            create_lef_tables(db_conn[key])

            for liberty_corner in scl_corners[variant]:
                key = f"{variant_name}_{View.Liberty.value}_{liberty_corner.value}"
                db_conn[key] = sqlite3.connect(":memory:")  
                create_lib_tables(db_conn[key])

    for variant in scl_variants:
        variant_name = cell_variant(pdk_name, [variant.name])[0]
        lef_paths = get_lef_paths(pdk_name, variant.value)

        for lef_path in lef_paths: 
            lef_parser = LefParser(lef_path)
            lef_parser.parse()

            if partition:
                key = f"{variant_name}_{View.Lef.value}"
                insert_lef_data(db_conn[key], lef_parser.macro_dict, scl_variant=variant_name)
                drop_cell_library_column(db_conn[key])
            else:
                insert_lef_data(db_conn["single"], lef_parser.macro_dict, scl_variant=variant_name)

        for tlef_corner in techlef_corners:
            techlef_path = get_techlef_paths(pdk_name, variant.value, tlef_corner.value)
            tlef_parser = LefParser(techlef_path)
            tlef_parser.parse()

            if partition:
                key = f"{variant_name}_{View.TechLef.value}_{tlef_corner.value}"
                insert_tlef_data(db_conn[key], tlef_parser.layer_dict, tlef_parser.via_dict, corner=tlef_corner.value, scl_variant=variant_name)
                drop_cell_library_corner_columns(db_conn[key])
            else:
                insert_tlef_data(db_conn["single"], tlef_parser.layer_dict, tlef_parser.via_dict, corner=tlef_corner.value, scl_variant=variant_name)

        for liberty_corner in scl_corners[variant.value]:
            print(liberty_corner)
            corner_path = get_corner_path(pdk_name, variant_name, liberty_corner.value)

            print(corner_path)
            cells, operating_conditions = parse_liberty_file(corner_path)

            if partition: 
                key = f"{variant_name}_{View.Liberty.value}_{liberty_corner.value}"
                insert_lib_data(db_conn[key], cells, operating_conditions, cell_varaint=variant_name)
                drop_cell_library_corner_column(db_conn[key])
            else: 
                insert_lib_data(db_conn['single'], cells, operating_conditions, cell_varaint=variant_name)

    if partition:
        for key, conn in db_conn.items():
            variant, tlef_corner, liberty_corner = key.split('_', 2)
            disk_file_path = os.path.join(output_dir, f'{variant}_{tlef_corner}_{liberty_corner}.db')
            with sqlite3.connect(disk_file_path) as disk_conn:
                conn.backup(disk_conn)
            print(f"Partitioned database for {key} written to {disk_file_path}")
    else:
        disk_file_path = os.path.join(output_dir, f"{pdk_name}_index.db")
        with sqlite3.connect(disk_file_path) as disk_conn:
            db_conn["single"].backup(disk_conn)
        print(f"Single in-memory database written to {disk_file_path}")

    for conn in db_conn.values():
        conn.commit()
        conn.close()

   

if __name__ == '__main__':
    main()