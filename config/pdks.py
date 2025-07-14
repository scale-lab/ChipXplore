import sys 

from config.sky130 import Sky130TechLefCorner, sky130_scl_corners, SCLVariants, get_sky130_corner_path, cell_variant_sky130, get_sky130_pdk_path, get_sky130_lib_paths, get_sky130_techlef_paths, get_sky130_lef_paths
from config.asap7nm import ASAP7TechLefCorner, asap7nm_scl_corners, ASAP7nmSCLVariants, get_asap7_corner_path, cell_variant_asap7nm, get_asap7nm_pdk_path, get_asap7nm_lib_paths, get_asap7nm_techlef_paths, get_asap7nm_lef_paths
from config.tsmc65nm import  TSMC65TechLefCorners, tsmc65_scl_corners, TSMC65nmSCLVariants, get_tsmc65_corner_path, cell_variant_tsmc65, get_tsmc65_pdk_path, get_tsmc65_lib_paths, get_tsmc65_techlef_paths, get_tsmc65_lef_paths
from config.gf12 import gf12_scl_corners, GF12TechLefCorners, GF12SCLVariants, get_gf12_corner_path, get_gf12_lib_paths, get_gf12_techlef_paths, cell_variant_gf12, get_gf12_lef_paths, get_gf12_pdk_path


def get_techlef_corners(pdk_name):
    if pdk_name == "sky130": 
        corners = Sky130TechLefCorner
    elif pdk_name == "asap7": 
        corners = ASAP7TechLefCorner
    elif pdk_name == "tsmc65":
        corners = TSMC65TechLefCorners
    elif pdk_name == "gf12":
        corners = GF12TechLefCorners
    else:
        print(f"Invalid PDK Name, {pdk_name}")
        sys.exit(0)
    return corners 

def get_pdk_path(pdk_name):
    if pdk_name == "sky130": 
        pdk_path = get_sky130_pdk_path()
    elif pdk_name == "asap7": 
        pdk_path = get_asap7nm_pdk_path()
    elif pdk_name == "tsmc65":
        pdk_path = get_tsmc65_pdk_path()
    elif pdk_name == "gf12":
        pdk_path = get_gf12_pdk_path()
    else:
        print(f"Invalid PDK Name, {pdk_name}")
        sys.exit(0)
 
    return pdk_path


def get_scl(pdk_name):
    if pdk_name == "sky130": 
        scl_variants = SCLVariants
    elif pdk_name == "asap7": 
        scl_variants = ASAP7nmSCLVariants
    elif pdk_name == "tsmc65": 
        scl_variants = TSMC65nmSCLVariants
    elif pdk_name == "gf12":
        scl_variants = GF12SCLVariants
    else:
        print("Invalid PDK Name ")
        sys.exit(0)

    return scl_variants 


def get_lef_paths(pdk_name, variant):
    pdk_path = get_pdk_path(pdk_name)
    if pdk_name == "sky130": 
        lef_paths = get_sky130_lef_paths(pdk_path, variant)
    elif pdk_name == "asap7":
        lef_paths = get_asap7nm_lef_paths(pdk_path, variant) 
    elif pdk_name == "tsmc65":
        lef_paths = get_tsmc65_lef_paths(pdk_path, variant)
    elif pdk_name == "gf12":
        lef_paths = get_gf12_lef_paths(pdk_path, variant)
    return lef_paths 

def get_lib_paths(pdk_name, variant):
    pdk_path = get_pdk_path(pdk_name)
    if pdk_name == "sky130": 
        lib_paths = get_sky130_lib_paths(pdk_path, variant)
    elif pdk_name == "asap7":
        lib_paths = get_asap7nm_lib_paths(pdk_path, variant) 
    elif pdk_name == "tsmc65":
        lib_paths = get_tsmc65_lib_paths(pdk_path, variant)
    elif pdk_name == "gf12":
        lib_paths = get_gf12_lib_paths(pdk_path, variant)

    return lib_paths 
 

def get_techlef_paths(pdk_name, variant, corner=None):
    pdk_path = get_pdk_path(pdk_name)
    if pdk_name == "sky130": 
        lef_paths = get_sky130_techlef_paths(pdk_path, variant, corner)
    elif pdk_name == "asap7":
        lef_paths = get_asap7nm_techlef_paths(pdk_path, variant) 
    elif pdk_name == "tsmc65":
        lef_paths = get_tsmc65_techlef_paths(pdk_path, corner) 
    elif pdk_name == "gf12":
        lef_paths = get_gf12_techlef_paths(pdk_path, variant)
    return lef_paths 
  


def cell_variant(pdk_name, scl_variants):
    if pdk_name == "sky130": 
        variants = cell_variant_sky130(scl_variants)
    elif pdk_name == "asap7":
        variants = cell_variant_asap7nm(scl_variants) 
    elif pdk_name == "tsmc65":
        variants = cell_variant_tsmc65(scl_variants) 
    elif pdk_name == "gf12":
        variants = cell_variant_gf12(scl_variants) 
    return variants 

def get_scl_corners(pdk_name):
    if pdk_name == "sky130": 
        scl_corners = sky130_scl_corners
    elif pdk_name == "asap7":
        scl_corners = asap7nm_scl_corners
    elif pdk_name == "tsmc65":
        scl_corners = tsmc65_scl_corners
    elif pdk_name == "gf12":
        scl_corners = gf12_scl_corners
    return scl_corners

def get_corner_path(pdk_name, scl_variant, corner):
    if pdk_name == "sky130":
        corner_path = get_sky130_corner_path(scl_variant, corner)
    elif pdk_name == "asap7":
        corner_path = get_asap7_corner_path(scl_variant, corner)
    elif pdk_name == "tsmc65":
        corner_path = get_tsmc65_corner_path(scl_variant, corner)
    elif pdk_name == "gf12":
        corner_path = get_gf12_corner_path(scl_variant, corner)
    return corner_path