import os 
from enum import Enum


def get_sky130_pdk_path():
    pdk_root = os.environ.get('PDK_ROOT')
    return os.path.join(pdk_root, 'sky130A', 'libs.ref') 


def get_sky130_lef_paths(pdk_path, variant): 
    lef_path = os.path.join(pdk_path, variant, 'lef', f"{variant}.lef")
    return [lef_path]


def get_sky130_lib_paths(pdk_path, variant):
    lib_path = os.path.join(pdk_path, variant, 'lib')
    return lib_path


def get_sky130_techlef_paths(pdk_path, variant, corner):
    techlef_path = os.path.join(pdk_path, variant, 'techlef', f"{variant}__{corner}.tlef")
    return techlef_path


def get_sky130_corner_path(variant, corner):
    pdk_path = get_sky130_pdk_path()
    corner_path = os.path.join(pdk_path, variant, 'lib', f'{variant}__{corner}.lib')
    return corner_path


class SCLVariants(Enum):
    HighDensity = "sky130_fd_sc_hd" 
    HighDensityLowLeakage = "sky130_fd_sc_hdll"
    LowSpeed = "sky130_fd_sc_ls"
    HighSpeed = "sky130_fd_sc_hs"
    MediumSpeed = "sky130_fd_sc_ms"
    LowPower = "sky130_fd_sc_lp"


class Sky130TechLefCorner(Enum):
    MIN = "min"
    MAX = "max"
    NOM = "nom"


class View(Enum):
    Liberty = "Liberty" 
    Lef = "Lef" 
    TechLef = "TechnologyLef"


class HD_PVTCorner(Enum):
    FF_100C_1V65 = "ff_100C_1v65"
    FF_100C_1V95 = "ff_100C_1v95"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V65 = "ff_n40C_1v65"
    FF_N40C_1V76 = "ff_n40C_1v76"
    FF_N40C_1V95 = "ff_n40C_1v95"
    SS_100C_1V40 = "ss_100C_1v40"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_N40C_1V28 = "ss_n40C_1v28"
    SS_N40C_1V35 = "ss_n40C_1v35"
    SS_N40C_1V40 = "ss_n40C_1v40"
    SS_N40C_1V44 = "ss_n40C_1v44"
    SS_N40C_1V60 = "ss_n40C_1v60"
    SS_N40C_1V76 = "ss_n40C_1v76"
    TT_025C_1V80 = "tt_025C_1v80"
    TT_100C_1V80 = "tt_100C_1v80"
    
    @classmethod
    def get_tt_corner(cls):
        return cls.TT_025C_1V80

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


def get_corner_name(scl_library: str, voltage: str, temperature: str):
    variant = SCLVariants(scl_library[0])
    temperature = str(int(float(temperature)))
    voltage = voltage.replace('.', 'v')
    corner_type = sky130_scl_corners[variant]

    for corner in corner_type: 
        if temperature in corner.value and voltage in corner.value:
            return corner.value
    
    return corner_type.get_tt_corner()
                


class HDLL_PVTCorner(Enum):
    FF_100C_1V65 = "ff_100C_1v65"
    FF_100C_1V95 = "ff_100C_1v95"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V65 = "ff_n40C_1v65"
    FF_N40C_1V95 = "ff_n40C_1v95"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_N40C_1V28 = "ss_n40C_1v28"
    SS_N40C_1V44 = "ss_n40C_1v44"
    SS_N40C_1V60 = "ss_n40C_1v60"
    SS_N40C_1V76 = "ss_n40C_1v76"
    TT_025C_1V80 = "tt_025C_1v80"
    
    @classmethod
    def get_tt_corner(cls):
        return cls.TT_025C_1V80

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]



class LS_PVTCorner(Enum):
    FF_085C_1V95 = "ff_085C_1v95"
    FF_100C_1V95 = "ff_100C_1v95"
    FF_150C_1V95 = "ff_150C_1v95"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V76 = "ff_n40C_1v76"
    FF_N40C_1V95 = "ff_n40C_1v95"
    SS_100C_1V40 = "ss_100C_1v40"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_150C_1V60 = "ss_150C_1v60"
    SS_N40C_1V28 = "ss_n40C_1v28"
    SS_N40C_1V35 = "ss_n40C_1v35"
    SS_N40C_1V40 = "ss_n40C_1v40"
    SS_N40C_1V44 = "ss_n40C_1v44"
    SS_N40C_1V60 = "ss_n40C_1v60"
    SS_N40C_1V76 = "ss_n40C_1v76"
    TT_025C_1V80 = "tt_025C_1v80"
    TT_100C_1V80 = "tt_100C_1v80"
   
    @classmethod
    def get_tt_corner(cls):
        return cls.TT_025C_1V80

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


class HS_PVTCorner(Enum):
    FF_100C_1V95 = "ff_100C_1v95"
    FF_150C_1V95 = "ff_150C_1v95"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V76 = "ff_n40C_1v76"
    FF_N40C_1V95 = "ff_n40C_1v95"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_150C_1V60 = "ss_150C_1v60"
    SS_N40C_1V28 = "ss_n40C_1v28"
    SS_N40C_1V44 = "ss_n40C_1v44"
    SS_N40C_1V60 = "ss_n40C_1v60"
    TT_025C_1V20 = "tt_025C_1v20"
    TT_025C_1V35 = "tt_025C_1v35"
    TT_025C_1V44 = "tt_025C_1v44"
    TT_025C_1V50 = "tt_025C_1v50"
    TT_025C_1V62 = "tt_025C_1v62"
    TT_025C_1V68 = "tt_025C_1v68"
    TT_025C_1V80 = "tt_025C_1v80"
    TT_025C_1V89 = "tt_025C_1v89"
    TT_025C_2V10 = "tt_025C_2v10"
    TT_100C_1V80 = "tt_100C_1v80"
    TT_150C_1V80 = "tt_150C_1v80"

    @classmethod
    def get_tt_corner(cls):
        return cls.TT_025C_1V80

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


class MS_PVTCorner(Enum):
    FF_100C_1V65 = "ff_100C_1v65"
    FF_100C_1V95 = "ff_100C_1v95"
    FF_150C_1V95 = "ff_150C_1v95"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V76 = "ff_n40C_1v76"
    FF_N40C_1V95 = "ff_n40C_1v95"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_150C_1V60 = "ss_150C_1v60"
    SS_N40C_1V28 = "ss_n40C_1v28"
    SS_N40C_1V44 = "ss_n40C_1v44"
    SS_N40C_1V60 = "ss_n40C_1v60"
    TT_025C_1V80 = "tt_025C_1v80"
    TT_100C_1V80 = "tt_100C_1v80" 

    @classmethod
    def get_tt_corner(cls):
        return cls.TT_025C_1V80

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


class LP_PVTCorner(Enum):
    FF_100C_1V95 = "ff_100C_1v95"
    FF_125C_3V15 = "ff_125C_3v15"
    FF_140C_1V95 = "ff_140C_1v95"
    FF_150C_2V05 = "ff_150C_2v05"
    FF_N40C_1V56 = "ff_n40C_1v56"
    FF_N40C_1V76 = "ff_n40C_1v76"
    FF_N40C_1V95 = "ff_n40C_1v95"
    FF_N40C_2V05 = "ff_n40C_2v05"
    SS_100C_1V60 = "ss_100C_1v60"
    SS_140C_1V65 = "ss_140C_1v65"
    SS_150C_1V65 = "ss_150C_1v65"
    SS_N40C_1V55 = "ss_n40C_1v55"
    SS_N40C_1V60 = "ss_n40C_1v60"
    SS_N40C_1V65 = "ss_n40C_1v65"

    @classmethod
    def get_tt_corner(cls):
        return cls.SS_N40C_1V55

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


sky130_scl_corners = {
    SCLVariants.HighDensity: HD_PVTCorner,
    SCLVariants.HighDensityLowLeakage: HDLL_PVTCorner,
    SCLVariants.LowSpeed: LS_PVTCorner,
    SCLVariants.HighSpeed: HS_PVTCorner,
    SCLVariants.MediumSpeed: MS_PVTCorner,
    SCLVariants.LowPower: LP_PVTCorner,
}

def cell_variant_sky130(scl_variants):
  prefix = {
    'HighDensity': 'sky130_fd_sc_hd',
    'HighDensityLowLeakage': 'sky130_fd_sc_hdll',
    'HighSpeed': 'sky130_fd_sc_hs',
    'LowSpeed': 'sky130_fd_sc_ls',
    'MediumSpeed': 'sky130_fd_sc_ms',
    'LowPower': 'sky130_fd_sc_lp'
  }
  
  scl_prefix = []
  for variant in scl_variants:
    scl_skyprefix = prefix[variant]
    scl_prefix.append(scl_skyprefix)
  
  return scl_prefix

