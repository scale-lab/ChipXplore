import os 
import glob 
from enum import Enum


class ASAP7TechLefCorner(Enum):
    MIN = "min"
    MAX = "max"
    NOM = "nom"



class ASAP7nmSCLVariants(Enum):
    T_26 = "asap7sc6t_26" 
    T_28 = "asap7sc7p5t_28"

class T26Corners(Enum):
    AO_LVT_FF = "AO_LVT_FF_nldm_211010"
    AO_LVT_SS = "AO_LVT_SS_nldm_211010"
    AO_LVT_TT = "AO_LVT_TT_nldm_211010"
    AO_RVT_FF = "AO_RVT_FF_nldm_211010"
    AO_RVT_SS = "AO_RVT_SS_nldm_211010"
    AO_RVT_TT = "AO_RVT_TT_nldm_211010"
    AO_SLVT_FF = "AO_SLVT_FF_nldm_211010"
    AO_SLVT_SS = "AO_SLVT_SS_nldm_211010"
    AO_SLVT_TT = "AO_SLVT_TT_nldm_211010"
    AO_SRAM_FF = "AO_SRAM_FF_nldm_211010"
    AO_SRAM_SS = "AO_SRAM_SS_nldm_211010"
    AO_SRAM_TT = "AO_SRAM_TT_nldm_211010"

    CKINVDC_LVT_FF = "CKINVDC_LVT_FF_nldm_211010"
    CKINVDC_LVT_SS = "CKINVDC_LVT_SS_nldm_211010"
    CKINVDC_LVT_TT = "CKINVDC_LVT_TT_nldm_211010"
    CKINVDC_RVT_FF = "CKINVDC_RVT_FF_nldm_211010"
    CKINVDC_RVT_SS = "CKINVDC_RVT_SS_nldm_211010"
    CKINVDC_RVT_TT = "CKINVDC_RVT_TT_nldm_211010"
    CKINVDC_SLVT_FF = "CKINVDC_SLVT_FF_nldm_211010"
    CKINVDC_SLVT_SS = "CKINVDC_SLVT_SS_nldm_211010"
    CKINVDC_SLVT_TT = "CKINVDC_SLVT_TT_nldm_211010"
    CKINVDC_SRAM_FF = "CKINVDC_SRAM_FF_nldm_211010"
    CKINVDC_SRAM_SS = "CKINVDC_SRAM_SS_nldm_211010"
    CKINVDC_SRAM_TT = "CKINVDC_SRAM_TT_nldm_211010"
    
    INVBUF_LVT_FF = "INVBUF_LVT_FF_nldm_211010"
    INVBUF_LVT_SS = "INVBUF_LVT_SS_nldm_211010"
    INVBUF_LVT_TT = "INVBUF_LVT_TT_nldm_211010"
    INVBUF_RVT_FF = "INVBUF_RVT_FF_nldm_211010"
    INVBUF_RVT_SS = "INVBUF_RVT_SS_nldm_211010"
    INVBUF_RVT_TT = "INVBUF_RVT_TT_nldm_211010"
    INVBUF_SLVT_FF = "INVBUF_SLVT_FF_nldm_211010"
    INVBUF_SLVT_SS = "INVBUF_SLVT_SS_nldm_211010"
    INVBUF_SLVT_TT = "INVBUF_SLVT_TT_nldm_211010"
    INVBUF_SRAM_FF = "INVBUF_SRAM_FF_nldm_211010"
    INVBUF_SRAM_SS = "INVBUF_SRAM_SS_nldm_211010"
    INVBUF_SRAM_TT = "INVBUF_SRAM_TT_nldm_211010"

    OA_LVT_FF = "OA_LVT_FF_nldm_211010"
    OA_LVT_SS = "OA_LVT_SS_nldm_211010"
    OA_LVT_TT = "OA_LVT_TT_nldm_211010"
    OA_RVT_FF = "OA_RVT_FF_nldm_211010"
    OA_RVT_SS = "OA_RVT_SS_nldm_211010"
    OA_RVT_TT = "OA_RVT_TT_nldm_211010"
    OA_SLVT_FF = "OA_SLVT_FF_nldm_211010"
    OA_SLVT_SS = "OA_SLVT_SS_nldm_211010"
    OA_SLVT_TT = "OA_SLVT_TT_nldm_211010"
    OA_SRAM_FF = "OA_SRAM_FF_nldm_211010"
    OA_SRAM_SS = "OA_SRAM_SS_nldm_211010"
    OA_SRAM_TT = "OA_SRAM_TT_nldm_211010"
    
    SIMPLE_LVT_FF = "SIMPLE_LVT_FF_nldm_211010"
    SIMPLE_LVT_SS = "SIMPLE_LVT_SS_nldm_211010"
    SIMPLE_LVT_TT = "SIMPLE_LVT_TT_nldm_211010"
    SIMPLE_RVT_FF = "SIMPLE_RVT_FF_nldm_211010"
    SIMPLE_RVT_SS = "SIMPLE_RVT_SS_nldm_211010"
    SIMPLE_RVT_TT = "SIMPLE_RVT_TT_nldm_211010"



class T28Corners(Enum):
    AO_LVT_FF = "AO_LVT_FF_nldm_211120"
    AO_LVT_SS = "AO_LVT_SS_nldm_211120"
    AO_LVT_TT = "AO_LVT_TT_nldm_211120"
    AO_RVT_FF = "AO_RVT_FF_nldm_211120"
    AO_RVT_SS = "AO_RVT_SS_nldm_211120"
    AO_RVT_TT = "AO_RVT_TT_nldm_211120"
    AO_SLVT_FF = "AO_SLVT_FF_nldm_211120"
    AO_SLVT_SS = "AO_SLVT_SS_nldm_211120"
    AO_SLVT_TT = "AO_SLVT_TT_nldm_211120"
    AO_SRAM_FF = "AO_SRAM_FF_nldm_211120"
    AO_SRAM_SS = "AO_SRAM_SS_nldm_211120"
    AO_SRAM_TT = "AO_SRAM_TT_nldm_211120"

    INVBUF_LVT_FF = "INVBUF_LVT_FF_nldm_220122"
    INVBUF_LVT_SS = "INVBUF_LVT_SS_nldm_220122"
    INVBUF_LVT_TT = "INVBUF_LVT_TT_nldm_220122"
    INVBUF_RVT_FF = "INVBUF_RVT_FF_nldm_220122"
    INVBUF_RVT_SS = "INVBUF_RVT_SS_nldm_220122"
    INVBUF_RVT_TT = "INVBUF_RVT_TT_nldm_220122"
    INVBUF_SLVT_FF = "INVBUF_SLVT_FF_nldm_220122"
    INVBUF_SLVT_SS = "INVBUF_SLVT_SS_nldm_220122"
    INVBUF_SLVT_TT = "INVBUF_SLVT_TT_nldm_220122"
    INVBUF_SRAM_FF = "INVBUF_SRAM_FF_nldm_220122"
    INVBUF_SRAM_SS = "INVBUF_SRAM_SS_nldm_220122"
    INVBUF_SRAM_TT = "INVBUF_SRAM_TT_nldm_220122"

    OA_LVT_FF = "OA_LVT_FF_nldm_211120"
    OA_LVT_SS = "OA_LVT_SS_nldm_211120"
    OA_LVT_TT = "OA_LVT_TT_nldm_211120"
    OA_RVT_FF = "OA_RVT_FF_nldm_211120"
    OA_RVT_SS = "OA_RVT_SS_nldm_211120"
    OA_RVT_TT = "OA_RVT_TT_nldm_211120"
    OA_SLVT_FF = "OA_SLVT_FF_nldm_211120"
    OA_SLVT_SS = "OA_SLVT_SS_nldm_211120"
    OA_SLVT_TT = "OA_SLVT_TT_nldm_211120"
    OA_SRAM_FF = "OA_SRAM_FF_nldm_211120"
    OA_SRAM_SS = "OA_SRAM_SS_nldm_211120"
    OA_SRAM_TT = "OA_SRAM_TT_nldm_211120"

    SEQ_LVT_FF = "SEQ_LVT_FF_nldm_220123"
    SEQ_LVT_SS = "SEQ_LVT_SS_nldm_220123"
    SEQ_LVT_TT = "SEQ_LVT_TT_nldm_220123"
    SEQ_RVT_FF = "SEQ_RVT_FF_nldm_220123"
    SEQ_RVT_SS = "SEQ_RVT_SS_nldm_220123"
    SEQ_RVT_TT = "SEQ_RVT_TT_nldm_220123"
    SEQ_SLVT_FF = "SEQ_SLVT_FF_nldm_220123"
    SEQ_SLVT_SS = "SEQ_SLVT_SS_nldm_220123"
    SEQ_SLVT_TT = "SEQ_SLVT_TT_nldm_220123"
    SEQ_SRAM_FF = "SEQ_SRAM_FF_nldm_220123"
    SEQ_SRAM_SS = "SEQ_SRAM_SS_nldm_220123"
    SEQ_SRAM_TT = "SEQ_SRAM_TT_nldm_220123"

    SIMPLE_LVT_FF = "SIMPLE_LVT_FF_nldm_211120"
    SIMPLE_LVT_SS = "SIMPLE_LVT_SS_nldm_211120"
    SIMPLE_LVT_TT = "SIMPLE_LVT_TT_nldm_211120"
    SIMPLE_RVT_FF = "SIMPLE_RVT_FF_nldm_211120"
    SIMPLE_RVT_SS = "SIMPLE_RVT_SS_nldm_211120"
    SIMPLE_RVT_TT = "SIMPLE_RVT_TT_nldm_211120"
    SIMPLE_SLVT_FF = "SIMPLE_SLVT_FF_nldm_211120"
    SIMPLE_SLVT_SS = "SIMPLE_SLVT_SS_nldm_211120"
    SIMPLE_SLVT_TT = "SIMPLE_SLVT_TT_nldm_211120"
    SIMPLE_SRAM_FF = "SIMPLE_SRAM_FF_nldm_211120"
    SIMPLE_SRAM_SS = "SIMPLE_SRAM_SS_nldm_211120"
    SIMPLE_SRAM_TT = "SIMPLE_SRAM_TT_nldm_211120"

def get_asap7nm_pdk_path():
    pdk_root= "/oscar/data/sreda/mabdelat/"
    return os.path.join(pdk_root, 'asap7') 
 

def get_asap7nm_lef_paths(pdk_path, variant):
    lef_dir = os.path.join(pdk_path, variant, 'LEF')
    lef_files = glob.glob(os.path.join(lef_dir, "*.lef"), recursive=False)
    return lef_files


def get_asap7nm_lib_paths(pdk_path, variant):
    lib_path = os.path.join(pdk_path, variant, 'LIB', 'NLDM')
    return lib_path 


def get_asap7nm_techlef_paths(pdk_path, variant):
    if variant == ASAP7nmSCLVariants.T_26.value:
        file_name = "asap7sc6t_tech_4x_210831"
    elif variant == ASAP7nmSCLVariants.T_28.value:
        file_name = "asap7_tech_1x_201209"

    techlef_path = os.path.join(pdk_path, variant, 'techlef_misc', f"{file_name}.lef")
    return techlef_path 

def get_asap7_corner_path(variant, corner):
    pdk_path = get_asap7nm_pdk_path()
    corner_path = os.path.join(pdk_path, variant, 'LIB', 'NLDM',  f'{variant[:-3]}_{corner}.lib')
    return corner_path

asap7nm_scl_corners = {
    ASAP7nmSCLVariants.T_26: T26Corners,
    ASAP7nmSCLVariants.T_28: T28Corners
}


def cell_variant_asap7nm(scl_variants):
  prefix = {
    'T_26': 'asap7sc6t_26',
    'T_28': 'asap7sc7p5t_28',
  }
  
  scl_prefix = []
  for variant in scl_variants:
    scl_skyprefix = prefix[variant]
    scl_prefix.append(scl_skyprefix)
  
  return scl_prefix
