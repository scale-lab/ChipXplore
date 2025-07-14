import os 
import sys 
from enum import Enum 


def get_gf12_pdk_path():
    path = "/home/manar/GF12/GF12LP/ARM_StdCells/14LPPXL"
    return path 


def get_gf12_techlef_paths(pdk_path, corner):
    techlef_path = os.path.join(pdk_path, "", corner, f"sc12_tech.lef")
    return techlef_path


def get_gf12_lef_paths(pdk_path, variant): 
    pdk_path = get_gf12_pdk_path()
    if variant == GF12SCLVariants.GF12_LP_LVT.value: 
        path = os.path.join(pdk_path, "LVT/GF37LB009-FE-00000-r0p0-03eac0/arm/gf/14lppxl/sc9mcpp84_base_lvt_c14/r0p0/lef/sc9mcpp84_14lppxl_base_lvt_c14.lef")
    elif variant == GF12SCLVariants.GF12_LP_SLVT.value: 
        path = os.path.join(pdk_path, "SLVT/GF37LB007-FB-00000-r0p0-03eac0/arm/gf/14lppxl/sc9mcpp84_base_slvt_c14/r0p0/lef/sc9mcpp84_14lppxl_base_slvt_c14.lef")
    else:
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)
    lef_path = os.path.join(pdk_path, path)
    return [lef_path]


def get_gf12_lib_paths(pdk_path, variant):
    pdk_path = get_gf12_pdk_path()
    if variant == GF12SCLVariants.GF12_LP_LVT.value: 
        lib_path = os.path.join(pdk_path, "LVT/GF37LB009-FE-00000-r0p0-03eac0/arm/gf/14lppxl/sc9mcpp84_base_lvt_c14/r0p0/lib") 
    elif variant == GF12SCLVariants.GF12_LP_SLVT.value: 
        lib_path = os.path.join(pdk_path, "SLVT/GF37LB007-FB-00000-r0p0-03eac0/arm/gf/14lppxl/sc9mcpp84_base_slvt_c14/r0p0/lib")  
    else: 
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)
    return lib_path
 

def get_gf12_corner_path(variant, corner):
    pdk_path = get_gf12_pdk_path()
    lib_path = get_gf12_lib_paths(pdk_path, variant)
    if variant == GF12SCLVariants.GF12_LP_LVT.value: 
        prefix = "sc9mcpp84_14lppxl_base_lvt_c14" 
    elif variant == GF12SCLVariants.GF12_LP_SLVT.value:
        prefix = "sc9mcpp84_14lppxl_base_slvt_c14"  
    else: 
        print(f"Invalid Variant Name: {variant}")
        sys.exit(0)
    corner_path = os.path.join(lib_path, f"{prefix}_{corner}.lib")
    return corner_path


class GF12TechLefCorners(Enum):
    pass 

class GF12SCLVariants(Enum):
    GF12_LP_LVT = "14LPPXL_LVT"
    GF12_LP_SLVT = "14LPPXL_SLVT"


class LP_LVT_PVTCorner(Enum):
    FFA_SIGCMIN_MIN_0P54V_M55C = "ffa_sigcmin_min_0p54v_m55c"
    FFA_SIGCMIN_MIN_0P88V_M40C = "ffa_sigcmin_min_0p88v_m40c"
    SSA_SIGCMAX_MAX_0P66V_M55C = "ssa_sigcmax_max_0p66v_m55c"
    FFA_SIGCMIN_MIN_0P66V_125C = "ffa_sigcmin_min_0p66v_125c"
    NN_NOMINAL_MAX_0P60V_25C   = "nn_nominal_max_0p60v_25c"
    SSA_SIGCMAX_MAX_0P72V_125C = "ssa_sigcmax_max_0p72v_125c"
    FFA_SIGCMIN_MIN_0P66V_M40C = "ffa_sigcmin_min_0p66v_m40c"
    NN_NOMINAL_MAX_0P80V_25C   = "nn_nominal_max_0p80v_25c"
    SSA_SIGCMAX_MAX_0P72V_M40C = "ssa_sigcmax_max_0p72v_m40c"
    FFA_SIGCMIN_MIN_0P77V_M55C = "ffa_sigcmin_min_0p77v_m55c"
    SSA_SIGCMAX_MAX_0P54V_125C = "ssa_sigcmax_max_0p54v_125c"
    FFA_SIGCMIN_MIN_0P88V_125C = "ffa_sigcmin_min_0p88v_125c"
    SSA_SIGCMAX_MAX_0P54V_M40C = "ssa_sigcmax_max_0p54v_m40c"


class LP_SLVT_PVTCorner(Enum):
    FFA_SIGCMIN_MIN_0P54V_M55C = "ffa_sigcmin_min_0p54v_m55c"
    FFA_SIGCMIN_MIN_0P88V_M55C = "ffa_sigcmin_min_0p88v_m55c"
    SSA_SIGCMAX_MAX_0P63V_125C = "ssa_sigcmax_max_0p63v_125c"
    FFA_SIGCMIN_MIN_0P59V_M55C = "ffa_sigcmin_min_0p59v_m55c"
    FFA_SIGCMIN_MIN_0P945V_125C = "ffa_sigcmin_min_0p945v_125c"
    SSA_SIGCMAX_MAX_0P63V_M40C  = "ssa_sigcmax_max_0p63v_m40c"
    FFA_SIGCMIN_MIN_0P63V_M55C  = "ffa_sigcmin_min_0p63v_m55c"
    FFA_SIGCMIN_MIN_0P945V_M40C = "ffa_sigcmin_min_0p945v_m40c"
    SSA_SIGCMAX_MAX_0P63V_M55C  = "ssa_sigcmax_max_0p63v_m55c"
    FFA_SIGCMIN_MIN_0P66V_125C  = "ffa_sigcmin_min_0p66v_125c"
    FFA_SIGCMIN_MIN_0P945V_M55C = "ffa_sigcmin_min_0p945v_m55c"
    SSA_SIGCMAX_MAX_0P66V_M55C = "ssa_sigcmax_max_0p66v_m55c"
    FFA_SIGCMIN_MIN_0P66V_M40C = "ffa_sigcmin_min_0p66v_m40c"
    FFA_SIGCMIN_MIN_0P99V_M55C = "ffa_sigcmin_min_0p99v_m55c"
    SSA_SIGCMAX_MAX_0P72V_125C = "ssa_sigcmax_max_0p72v_125c"
    NN_NOMINAL_MAX_0P60V_25C   = "nn_nominal_max_0p60v_25c"
    SSA_SIGCMAX_MAX_0P72V_M40C = "ssa_sigcmax_max_0p72v_m40c"
    FFA_SIGCMIN_MIN_0P72V_M55C = "ffa_sigcmin_min_0p72v_m55c"
    NN_NOMINAL_MAX_0P70V_25C = "nn_nominal_max_0p70v_25c"
    SSA_SIGCMAX_MAX_0P72V_M55C = "ssa_sigcmax_max_0p72v_m55c"
    FFA_SIGCMIN_MIN_0P77V_125C = "ffa_sigcmin_min_0p77v_125c"
    NN_NOMINAL_MAX_0P80V_25C = "nn_nominal_max_0p80v_25c"
    SSA_SIGCMAX_MAX_0P81V_125C = "ssa_sigcmax_max_0p81v_125c"
    FFA_SIGCMIN_MIN_0P77V_M40C = "ffa_sigcmin_min_0p77v_m40c"
    NN_NOMINAL_MAX_0P90V_25C = "nn_nominal_max_0p90v_25c"
    SSA_SIGCMAX_MAX_0P81V_M40C = "ssa_sigcmax_max_0p81v_m40c"
    FFA_SIGCMIN_MIN_0P77V_M55C = "ffa_sigcmin_min_0p77v_m55c"
    SSA_SIGCMAX_MAX_0P54V_125C = "ssa_sigcmax_max_0p54v_125c"
    SSA_SIGCMAX_MAX_0P81V_M55C = "ssa_sigcmax_max_0p81v_m55c"
    FFA_SIGCMIN_MIN_0P81V_M55C = "ffa_sigcmin_min_0p81v_m55c"
    SSA_SIGCMAX_MAX_0P54V_M40C = "ssa_sigcmax_max_0p54v_m40c"
    SSA_SIGCMAX_MAX_0P88V_M55C = "ssa_sigcmax_max_0p88v_m55c"
    FFA_SIGCMIN_MIN_0P88V_125C = "ffa_sigcmin_min_0p88v_125c"
    FFA_SIGCMIN_MIN_0P88V_M40C = "ffa_sigcmin_min_0p88v_m40c"
    SSA_SIGCMAX_MAX_0P59V_M55C = "ssa_sigcmax_max_0p59v_m55c"


gf12_scl_corners = {
    GF12SCLVariants.GF12_LP_LVT.value: LP_LVT_PVTCorner,
    GF12SCLVariants.GF12_LP_SLVT.value: LP_SLVT_PVTCorner
}


def cell_variant_gf12(scl_variants):
    prefix = {
        'GF12_LP_LVT': '14LPPXL_LVT',
        'GF12_LP_SLVT': '14LPPXL_SLVT'
    }
    scl_prefix = []
    for variant in scl_variants:
        scl_skyprefix = prefix[variant]
        scl_prefix.append(scl_skyprefix)
    
    return scl_prefix
