import argparse
import json
import os
import subprocess
import csv
from typing import Any

GUROBI_N_VALUES = [32, 40, 44, 45]
CPLEX_N_VALUES = [25, 30, 31, 32]

def run_solver(solver_name: str, n: int) -> dict[str, Any]:
    module = "src.gurobi.solver" if solver_name == "gurobi" else "src.cplex_mip.solver"
    cmd = [
        "python", "-m", module,
        "--n", str(n),
        "--time-limit", "300",
        "--threads", "1",
        "--random-seed", "0",
        "--json"
    ]
    
    try:
        # 315 external timeout
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=315
        )
        
        # Try parsing JSON from stdout
        try:
            result = json.loads(process.stdout.strip())
        except json.JSONDecodeError:
            # Fallback if json decoding fails
            result = {
                "solver": "Gurobi Optimizer" if solver_name == "gurobi" else "IBM ILOG CPLEX",
                "method": f"{solver_name.upper()} MIP",
                "n": n,
                "status": "ERROR",
                "error": f"JSON Decode Error. Stdout: {process.stdout}. Stderr: {process.stderr}"
            }
            
        return result
            
    except subprocess.TimeoutExpired:
        return {
            "solver": "Gurobi Optimizer" if solver_name == "gurobi" else "IBM ILOG CPLEX",
            "method": f"{solver_name.upper()} MIP",
            "n": n,
            "status": "TIMEOUT",
            "error": "External timeout 315 seconds exceeded"
        }
    except Exception as e:
        return {
            "solver": "Gurobi Optimizer" if solver_name == "gurobi" else "IBM ILOG CPLEX",
            "method": f"{solver_name.upper()} MIP",
            "n": n,
            "status": "ERROR",
            "error": str(e)
        }

def normalize_result(solver_name: str, n: int, raw: dict[str, Any]) -> dict[str, Any]:
    status = raw.get("status", "UNKNOWN")
    has_solution = raw.get("has_solution")
    valid = raw.get("valid")
    positions = raw.get("positions")
    
    queen_count = len(positions) if positions is not None else None
    
    error_data = raw.get("error")
    error_category = None
    if error_data:
        if isinstance(error_data, dict):
            error_category = error_data.get("category", str(error_data))
        else:
            error_category = str(error_data)
            
    return {
        "solver": raw.get("solver", solver_name),
        "n": raw.get("n", n),
        "binary_variables": raw.get("binary_variables"),
        "linear_constraints": raw.get("linear_constraints"),
        "native_status": raw.get("native_status"),
        "status": status,
        "has_solution": has_solution,
        "valid": valid,
        "queen_count": queen_count,
        "build_time": raw.get("build_time"),
        "solve_time": raw.get("solve_time"),
        "total_time": raw.get("total_time"),
        "statistics": raw.get("statistics", {}),
        "error_category": error_category,
        "error_detail": error_data
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", choices=["gurobi", "cplex", "all"], default="all")
    args = parser.parse_args()
    
    os.makedirs("results/raw", exist_ok=True)
    os.makedirs("results/processed", exist_ok=True)
    
    results_raw = []
    results_normalized = []
    
    if args.solver in ("gurobi", "all"):
        for n in GUROBI_N_VALUES:
            print(f"Running Gurobi N={n}...")
            raw = run_solver("gurobi", n)
            results_raw.append(raw)
            norm = normalize_result("gurobi", n, raw)
            results_normalized.append(norm)
            print(f"  -> {norm['status']}")

    if args.solver in ("cplex", "all"):
        for n in CPLEX_N_VALUES:
            print(f"Running CPLEX N={n}...")
            raw = run_solver("cplex", n)
            results_raw.append(raw)
            norm = normalize_result("cplex", n, raw)
            results_normalized.append(norm)
            print(f"  -> {norm['status']}")
            
    with open("results/raw/mip_license_limits.json", "w") as f:
        json.dump(results_raw, f, indent=2)
        
    csv_columns = [
        "solver", "n", "binary_variables", "linear_constraints",
        "native_status", "status", "valid", "queen_count",
        "build_time", "solve_time", "total_time", "error_category"
    ]
    
    with open("results/processed/mip_license_limits.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for r in results_normalized:
            row = {k: r.get(k) for k in csv_columns}
            writer.writerow(row)
            
    print("Done. Results saved to results/raw/mip_license_limits.json and results/processed/mip_license_limits.csv.")

if __name__ == "__main__":
    main()

