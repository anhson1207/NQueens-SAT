import sys
import platform
import subprocess
from typing import Dict, Any

def get_system_metadata() -> Dict[str, Any]:
    meta = {
        "operating_system": platform.system(),
        "operating_system_version": platform.release(),
        "machine_architecture": platform.machine(),
        "python_version": sys.version.split(" ")[0],
    }
    try:
        import psutil
        meta["cpu_count"] = psutil.cpu_count(logical=True)
        meta["memory_information"] = f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
    except ImportError:
        pass
        
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        meta["git_commit_hash"] = commit
        meta["git_worktree_dirty"] = bool(dirty)
    except Exception:
        meta["git_commit_hash"] = "N/A"
        meta["git_worktree_dirty"] = "N/A"
        
    return meta

def get_solver_versions() -> Dict[str, str]:
    versions = {}
    
    # PySAT
    try:
        import pysat
        versions["pysat_version"] = "available" # PySAT doesn't easily expose __version__
    except ImportError:
        versions["pysat_version"] = "N/A"
        
    # OR-Tools
    try:
        import ortools
        versions["ortools_version"] = getattr(ortools, "__version__", "available")
    except ImportError:
        versions["ortools_version"] = "N/A"
        
    # Gurobi
    try:
        import gurobipy as gp
        versions["gurobi_version"] = ".".join(map(str, gp.gurobi.version()))
    except ImportError:
        versions["gurobi_version"] = "N/A"
        
    # DOcplex (CPLEX MIP / CP)
    try:
        import docplex
        versions["docplex_version"] = getattr(docplex, "__version__", "available")
    except ImportError:
        versions["docplex_version"] = "N/A"
        
    # CPLEX (Engine)
    try:
        import cplex
        versions["cplex_version"] = cplex.Cplex().get_version()
    except Exception:
        versions["cplex_version"] = "N/A"
        
    versions["cp_optimizer_version"] = "N/A" # Usually tied to DOcplex/CPLEX installation
    
    return versions

def get_full_environment_metadata() -> Dict[str, Any]:
    meta = get_system_metadata()
    meta.update(get_solver_versions())
    return meta

