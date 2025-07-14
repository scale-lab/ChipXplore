import os 
import sys
from enum import Enum 


def get_tsmc65_pdk_path():
    path = "/home/manar/TSMC65/65nm/ARM_std"
    return path 


def get_tsmc65_techlef_paths(pdk_path, corner):
    techlef_path = os.path.join(pdk_path, "TSMC_CLN65GP_Routing_Technology_Kit/arm/tsmc/cln65gp/arm_tech/r4p0/lef", corner, f"sc12_tech.lef")
    return techlef_path


def get_tsmc65_lef_paths(pdk_path, variant): 
    pdk_path = get_tsmc65_pdk_path()
    if variant == TSMC65nmSCLVariants.SC8_GP_HVT.value:
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC8/arm/tsmc/cln65gp/tsmc65_hvt_sc_metro/r2p0-00eac0/lef/scmetro_cln65hvt_macros.lef") 
        lef_path = [os.path.join(pdk_path, path)]
    elif variant == TSMC65nmSCLVariants.SC8_GP_RVT.value:
        path =  os.path.join(pdk_path, "TSMC_CLN65GP_SC8/arm/tsmc/cln65gp/tsmc65_rvt_sc_metro/r2p0-00eac0/lef/scmetro_cln65rvt_macros.lef") 
        lef_path = [os.path.join(pdk_path, path)]
   
    elif variant == TSMC65nmSCLVariants.SC10_GP_HVT.value:
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10/lef/tsmc65_hvt_sc_adv10_macro.lef") 
        lef_path = [os.path.join(pdk_path, path)]
    elif variant == TSMC65nmSCLVariants.SC10_GP_LVT.value:
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10/lef/tsmc65_lvt_sc_adv10_macro.lef") 
        lef_path = [os.path.join(pdk_path, path)]
    elif variant == TSMC65nmSCLVariants.SC10_PMK.value:
        path1 = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10-pmk/lef/tsmc65hvt_adv10pmk_macro.lef") 
        path2 = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10-pmk/lef/tsmc65lvt_adv10pmk_macro.lef") 
        path3 = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10-pmk/lef/tsmc65rvt_adv10pmk_macro.lef") 
        lef_path = [os.path.join(pdk_path, path1), os.path.join(pdk_path, path2), os.path.join(pdk_path, path3)]
   
    elif variant == TSMC65nmSCLVariants.SC12_GP_RVT.value: 
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gp/sc12_pmk_rvt/r2p0-00eac0/lef/tsmc-cln65rvt_adv12pmk_macro.lef")
        lef_path = [os.path.join(pdk_path, path)]
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_LVT.value: 
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gplus/sc12_base_lvt/r3p0-00eac0/lef/sc12_cln65gplus_base_lvt.lef")
        lef_path = [os.path.join(pdk_path, path)]
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_RVT.value: 
        path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gplus/sc12_base_rvt/r3p0-00eac0/lef/sc12_cln65gplus_base_rvt.lef")
        lef_path = [os.path.join(pdk_path, path)]
    else:
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)

    return lef_path


def get_tsmc65_lib_paths(pdk_path, variant):
    pdk_path = get_tsmc65_pdk_path()
    if variant == TSMC65nmSCLVariants.SC8_GP_HVT.value:
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC8/arm/tsmc/cln65gp/tsmc65_hvt_sc_metro/r2p0-00eac0/synopsys")
    elif variant == TSMC65nmSCLVariants.SC8_GP_RVT.value:
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC8/arm/tsmc/cln65gp/tsmc65_rvt_sc_metro/r2p0-00eac0/synopsys")
    elif variant == TSMC65nmSCLVariants.SC10_GP_HVT.value:
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10/synopsys")
    elif variant == TSMC65nmSCLVariants.SC10_GP_LVT.value:
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10/synopsys")
    elif variant == TSMC65nmSCLVariants.SC10_PMK.value:
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC10/aci/sc-ad10-pmk/synopsys") 
    elif variant == TSMC65nmSCLVariants.SC12_GP_RVT.value: 
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gp/sc12_pmk_rvt/r2p0-00eac0/synopsys")
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_LVT.value: 
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gplus/sc12_base_lvt/r3p0-00eac0/lib") 
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_RVT.value: 
        lib_path = os.path.join(pdk_path, "TSMC_CLN65GP_SC12/arm/tsmc/cln65gplus/sc12_base_rvt/r3p0-00eac0/lib")
    else: 
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)

    return lib_path


def get_tsmc65_corner_path(variant, corner):
    pdk_path = get_tsmc65_pdk_path()
    lib_path = get_tsmc65_lib_paths(pdk_path, variant)
    if variant == TSMC65nmSCLVariants.SC8_GP_HVT.value: 
        prefix = "scmetro_cln65gp" 
    elif variant == TSMC65nmSCLVariants.SC8_GP_RVT.value: 
        prefix = "scmetro_cln65gp"
    elif variant == TSMC65nmSCLVariants.SC10_GP_HVT.value: 
        prefix = "scadv10_cln65gp"
    elif variant == TSMC65nmSCLVariants.SC10_GP_LVT.value: 
        prefix = "scadv10_cln65gp"
    elif variant == TSMC65nmSCLVariants.SC10_PMK.value: 
        prefix = "scadv10pmk_tsmc65gp"
    elif variant == TSMC65nmSCLVariants.SC12_GP_RVT.value: 
        prefix = "scadv12pmk_tsmc65gp"
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_LVT.value: 
        prefix = "sc12_cln65gplus_base"
    elif variant == TSMC65nmSCLVariants.SC12_GPLUS_RVT.value: 
        prefix = "sc12_cln65gplus_base_rvt"
    else:
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)
    corner_path = os.path.join(lib_path, f"{prefix}_{corner}.lib")
    return corner_path




class TSMC65TechLefCorners(Enum):
    M6_3X2Z = "CN65S_6M_3X2Z"
    M6_4X1Z = "CN65S_6M_4X1Z"
    M7_4X2Y = "CN65S_7M_4X2Y"
    M7_4X2Z = "CN65S_7M_4X2Z"
    M7_5X1Z = "CN65S_7M_5X1Z"
    M8_5X2Z = "CN65S_8M_5X2Z"
    M8_6X1Z = "CN65S_8M_6X1Z"
    M9_6X2Z = "CN65S_9M_6X2Z"


class TSMC65nmSCLVariants(Enum):
    SC8_GP_HVT = "sc8_cln65gp_hvt"
    SC8_GP_RVT = "sc8_cln65gp_rvt"

    SC10_GP_HVT = "sc10_cln65gp_hvt"
    SC10_GP_LVT = "sc10_cln65gp_lvt"
    SC10_PMK = "sc10_pmk"
    
    SC12_GP_RVT = "cln65gp"
    SC12_GPLUS_LVT = "cln65gplus_lvt"
    SC12_GPLUS_RVT = "cln65gplus_rvt"


class SC8_GP_HVT_PVTCorner(Enum):
    FF_1P1V_M40C = "hvt_ff_1p1v_m40c"
    FF_1P1V_125C = "hvt_ff_1p1v_125c"
    FF_1P1V_0C   = "hvt_ff_1p1v_0c"
    TT_1P0V_25C  = "hvt_tt_1p0v_25c"
    SS_0P9V_125C = "hvt_ss_0p9v_125c" 


class SC8_GP_RVT_PVTCorner(Enum):
    FF_1P1V_M40C = "rvt_ff_1p1v_m40c"
    FF_1P1V_125C = "rvt_ff_1p1v_125c"
    FF_1P1V_0C   = "rvt_ff_1p1v_0c"
    TT_1P0V_25C  = "rvt_tt_1p0v_25c"
    SS_0P9V_125C = "rvt_ss_0p9v_125c"


class SC10_GP_HVT_PVTCorner(Enum):
    HVT_FF_1P1V_0C   = "hvt_ff_1p1v_0c"
    HVT_FF_1P1V_125C = "hvt_ff_1p1v_125c"
    HVT_FF_1P1V_m40C = "hvt_ff_1p1v_m40c"
    HVT_SS_0P9V_125C = "hvt_ss_0p9v_125c"
    HVT_TT_1P0V_25C  = "hvt_tt_1p0v_25c"



class SC10_GP_LVT_PVTCorner(Enum):
    LVT_FF_1P1V_M40C = "lvt_ff_1p1v_m40c"
    LVT_SS_0P9V_125C = "lvt_ss_0p9v_125c"
    LVT_FF_1P1V_0C   = "lvt_ff_1p1v_0c"
    LVT_SS_0P9V_M40C = "lvt_ss_0p9v_m40c"
    LVT_FF_1P1V_125C = "lvt_ff_1p1v_125c"
    LVT_TT_1P0V_25C  = "lvt_tt_1p0v_25c"



class SC10_GP_PMK_PVTCorner(Enum):
    HVT_SS_0P9V_M40C      = "hvt_ss_0p9v_m40c"
    LVT_SS_0P9V_1P0V_125C = "lvt_ss_0p9v_1p0v_125c"
    RVT_FF_1P1V_M40C      = "rvt_ff_1p1v_m40c"
    HVT_FF_1P1V_0C        = "hvt_ff_1p1v_0c"
    HVT_TT_1P0V_1P1V_25C  = "hvt_tt_1p0v_1p1v_25c"
    LVT_SS_0P9V_1P1V_125C = "lvt_ss_0p9v_1p1v_125c"
    RVT_SS_0P9V_125C      = "rvt_ss_0p9v_125c"
    HVT_FF_1P1V_125C      = "hvt_ff_1p1v_125c"
    HVT_TT_1P0V_25C       = "hvt_tt_1p0v_25c"
    LVT_SS_0P9V_M40C      = "lvt_ss_0p9v_m40c"
    RVT_SS_0P9V_1P0V_125C = "rvt_ss_0p9v_1p0v_125c"
    HVT_FF_1P1V_M40C      = "hvt_ff_1p1v_m40c"
    LVT_FF_1P1V_0C        = "lvt_ff_1p1v_0c"
    LVT_TT_1P0V_1P1V_25C  = "lvt_tt_1p0v_1p1v_25c"
    RVT_SS_0P9V_1P1V_125C = "rvt_ss_0p9v_1p1v_125c"
    HVT_SS_0P9V_125C      = "hvt_ss_0p9v_125c"
    LVT_FF_1P1V_125C      = "lvt_ff_1p1v_125c"
    LVT_TT_1P0V_25C       = "lvt_tt_1p0v_25c"
    RVT_SS_0P9V_M40C      = "rvt_ss_0p9v_m40c"
    HVT_SS_0P9V_1P0V_125C = "hvt_ss_0p9v_1p0v_125c"
    LVT_FF_1P1V_M40C      = "lvt_ff_1p1v_m40c"
    RVT_FF_1P1V_0C        = "rvt_ff_1p1v_0c"
    RVT_TT_1P0V_1P1V_25C  = "rvt_tt_1p0v_1p1v_25c"
    HVT_SS_0P9V_1P1V_125C = "hvt_ss_0p9v_1p1v_125c"
    LVT_SS_0P9V_125C      = "lvt_ss_0p9v_125c"
    RVT_FF_1P1V_125C      = "rvt_ff_1p1v_125c"
    RVT_TT_1P0V_25C       = "rvt_tt_1p0v_25c"



class SC12_GP_RVT_PVTCorner(Enum):
    FF_0C_1P1V = "rvt_ff_1p1v_0c"
    FF_125C_1P1V = "rvt_ff_1p1v_125c"
    FF_M40C_1P1V = "rvt_ff_1p1v_m40c"
    SS_125C_0P9V = "rvt_ss_0p9v_125c"
    SS_125C_0P9V_1P0V = "rvt_ss_0p9v_1p0v_125c"
    SS_125C_0P9V_1P1V = "rvt_ss_0p9v_1p1v_125c"
    TT_25C_1P0V = "rvt_tt_1p0v_25c"
    TT_25C_1P0V_1P1V = "rvt_tt_1p0v_1p1v_25c"

    @classmethod
    def get_tt_corner(cls):
        return cls.TT_25C_1P0V_1P1V

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]

class SC12_GPLUS_RVT_PVTCorner(Enum):
    FF_0C_1P10V = "ff_typical_min_1p10v_0c"
    FF_125C_1P10V = "ff_typical_min_1p10v_125c"
    FF_M40C_1P10V = "ff_typical_min_1p10v_m40c"
    SS_125C_0P90V = "ss_typical_max_0p90v_125c"
    SS_M40C_0P90V = "ss_typical_max_0p90v_m40c"
    TT_25C_1P00V = "tt_typical_max_1p00v_25c"

    @classmethod
    def get_tt_corner(cls):
        return cls.TT_25C_1P00V

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


class SC12_GPLUS_LVT_PVTCorner(Enum):
    FF_0C_1P10V = "lvt_ff_typical_min_1p10v_0c"
    FF_125C_1P10V = "lvt_ff_typical_min_1p10v_125c"
    FF_M40C_1P10V = "lvt_ff_typical_min_1p10v_m40c"
    SS_125C_0P90V = "lvt_ss_typical_max_0p90v_125c"
    SS_M40C_0P90V = "lvt_ss_typical_max_0p90v_m40c"
    TT_25C_1P00V = "lvt_tt_typical_max_1p00v_25c"

    @classmethod
    def get_tt_corner(cls):
        return cls.TT_25C_1P00V

    @classmethod
    def list_corners(cls):
        return [corner.value for corner in cls]


tsmc65_scl_corners = {
    TSMC65nmSCLVariants.SC8_GP_HVT.value: SC8_GP_HVT_PVTCorner,
    TSMC65nmSCLVariants.SC8_GP_RVT.value: SC8_GP_RVT_PVTCorner,
    
    TSMC65nmSCLVariants.SC10_GP_HVT.value: SC10_GP_HVT_PVTCorner,
    TSMC65nmSCLVariants.SC10_GP_LVT.value: SC10_GP_LVT_PVTCorner,
    TSMC65nmSCLVariants.SC10_PMK.value: SC10_GP_PMK_PVTCorner,


    TSMC65nmSCLVariants.SC12_GP_RVT.value: SC12_GP_RVT_PVTCorner,
    TSMC65nmSCLVariants.SC12_GPLUS_LVT.value: SC12_GPLUS_LVT_PVTCorner,
    TSMC65nmSCLVariants.SC12_GPLUS_RVT.value: SC12_GPLUS_RVT_PVTCorner,
}



def cell_variant_tsmc65(scl_variants):
  prefix = {
    'SC8_GP_HVT': 'sc8_cln65gp_hvt',
    'SC8_GP_RVT': 'sc8_cln65gp_rvt',
    
    'SC10_GP_HVT': 'sc10_cln65gp_hvt',
    'SC10_GP_LVT': 'sc10_cln65gp_lvt',
    'SC10_PMK': 'sc10_pmk',

    'SC12_GP_RVT': 'cln65gp',
    'SC12_GPLUS_LVT': 'cln65gplus_lvt',
    'SC12_GPLUS_RVT': 'cln65gplus_rvt',

  }
  
  scl_prefix = []
  for variant in scl_variants:
    scl_skyprefix = prefix[variant]
    scl_prefix.append(scl_skyprefix)
  
  return scl_prefix
