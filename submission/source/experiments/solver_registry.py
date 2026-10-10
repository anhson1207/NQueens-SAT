import sys
from typing import Dict, Any, List, Optional

METHODS = [
    "sat_pairwise",
    "sat_binary",
    "sat_sequential",
    "sat_commander",
    "sat_product",
    "cp_sat",
    "gurobi_mip",
    "cplex_mip",
    "cplex_cp",
]

REGISTRY = {
    "sat_pairwise": {
        "method_id": "sat_pairwise",
        "method_family": "SAT",
        "solver_name": "Glucose3",
        "module": "src.sat.solver",
        "encoding": "pairwise",
        "default_workers": 1,
        "license_limited": False,
    },
    "sat_binary": {
        "method_id": "sat_binary",
        "method_family": "SAT",
        "solver_name": "Glucose3",
        "module": "src.sat.solver",
        "encoding": "binary",
        "default_workers": 1,
        "license_limited": False,
    },
    "sat_sequential": {
        "method_id": "sat_sequential",
        "method_family": "SAT",
        "solver_name": "Glucose3",
        "module": "src.sat.solver",
        "encoding": "sequential",
        "default_workers": 1,
        "license_limited": False,
    },
    "sat_commander": {
        "method_id": "sat_commander",
        "method_family": "SAT",
        "solver_name": "Glucose3",
        "module": "src.sat.solver",
        "encoding": "commander",
        "default_workers": 1,
        "license_limited": False,
    },
    "sat_product": {
        "method_id": "sat_product",
        "method_family": "SAT",
        "solver_name": "Glucose3",
        "module": "src.sat.solver",
        "encoding": "product",
        "default_workers": 1,
        "license_limited": False,
    },
    "cp_sat": {
        "method_id": "cp_sat",
        "method_family": "CP-SAT",
        "solver_name": "OR-Tools CP-SAT",
        "module": "src.cp_sat.solver",
        "encoding": None,
        "default_workers": 1,
        "license_limited": False,
    },
    "gurobi_mip": {
        "method_id": "gurobi_mip",
        "method_family": "MIP",
        "solver_name": "Gurobi Optimizer",
        "module": "src.gurobi.solver",
        "encoding": None,
        "default_workers": 1,
        "license_limited": True,
    },
    "cplex_mip": {
        "method_id": "cplex_mip",
        "method_family": "MIP",
        "solver_name": "IBM ILOG CPLEX",
        "module": "src.cplex_mip.solver",
        "encoding": None,
        "default_workers": 1,
        "license_limited": True,
    },
    "cplex_cp": {
        "method_id": "cplex_cp",
        "method_family": "CP",
        "solver_name": "IBM CP Optimizer",
        "module": "src.cplex_cp.solver",
        "encoding": None,
        "default_workers": 1,
        "license_limited": False,
    }
}

def build_cli_command(method_id: str, n: int, config: Dict[str, Any]) -> List[str]:
    """Builds the subprocess command list for a specific method."""
    if method_id not in REGISTRY:
        raise ValueError(f"Unknown method {method_id}")
    
    meta = REGISTRY[method_id]
    cmd = [sys.executable, "-m", meta["module"], "--n", str(n), "--json"]
    
    # 1. SAT specific
    if meta["method_family"] == "SAT":
        if meta["encoding"]:
            cmd.extend(["--encoding", meta["encoding"]])
        if "sat_phase_policy" in config and config["sat_phase_policy"]:
            cmd.extend(["--phase-policy", str(config["sat_phase_policy"])])
    
    # 2. Exact Solvers specific
    else:
        if "timeout" in config and config["timeout"] is not None:
            cmd.extend(["--time-limit", str(config["timeout"])])
            
        workers = config.get("workers", meta["default_workers"])
        if method_id in ("cp_sat", "cplex_cp"):
            cmd.extend(["--workers", str(workers)])
        elif method_id in ("gurobi_mip", "cplex_mip"):
            cmd.extend(["--threads", str(workers)])
            
        if "random_seed" in config and config["random_seed"] is not None:
            cmd.extend(["--random-seed", str(config["random_seed"])])
            
    return cmd
