import pandas as pd
from pathlib import Path
from typing import Dict, Any
from .plot_config import METHOD_LABELS

def export_all_tables(df: pd.DataFrame, output_dir: Path, experiment_metadata: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Table 1: SAT at N=100
    _export_table1_sat_n100(df, output_dir)
    
    # Table 2: Exact solvers summary
    _export_table2_exact_summary(df, output_dir)
    
    # Table 3: Nine-method comparison at N=20
    _export_table3_n20(df, output_dir)
    
    # Table 4: CNF structures N=100
    _export_table4_cnf_n100(df, output_dir)
    
    # Table 5: Completion status
    _export_table5_completion(df, output_dir)
    
    # Table 6: Experimental setup
    _export_table6_setup(experiment_metadata, output_dir)


def _export_table1_sat_n100(df: pd.DataFrame, output_dir: Path) -> None:
    n_val = 100
    sat_methods = ["sat_pairwise", "sat_binary", "sat_sequential", "sat_commander", "sat_product"]
    
    rows = []
    for method in sat_methods:
        method_df = df[(df["method_id"] == method) & (df["n"] == n_val)]
        if method_df.empty:
            continue
            
        success_runs = len(method_df[(method_df["status"] == "SAT") & (method_df["valid"] == True)])
        timeout_runs = len(method_df[method_df["status"] == "TIMEOUT"])
        
        # Take max for structural properties
        p_var = method_df["primary_variables"].max()
        a_var = method_df["auxiliary_variables"].max()
        clauses = method_df["clauses"].max()
        
        # Median runtime only for successful runs
        success_df = method_df[(method_df["status"] == "SAT") & (method_df["valid"] == True)]
        median_time = success_df["pipeline_total_time"].median() if not success_df.empty else pd.NA
        
        rows.append({
            "Encoding": METHOD_LABELS.get(method, method),
            "Primary Variables": p_var,
            "Auxiliary Variables": a_var,
            "Total Variables": p_var + a_var if pd.notna(p_var) and pd.notna(a_var) else pd.NA,
            "Clauses": clauses,
            "Successful Runs": success_runs,
            "Timeout Runs": timeout_runs,
            "Median Runtime": median_time
        })
        
    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "table01_sat_n100.csv", index=False)


def _export_table2_exact_summary(df: pd.DataFrame, output_dir: Path) -> None:
    exact_methods = ["or_tools_cp_sat", "gurobi_mip", "cplex_mip", "cplex_cp"]
    rows = []
    
    for method in exact_methods:
        method_df = df[df["method_id"] == method]
        if method_df.empty:
            continue
            
        success_df = method_df[(method_df["status"] == "SAT") & (method_df["valid"] == True)]
        largest_sat_n = success_df["n"].max() if not success_df.empty else pd.NA
        
        n100_df = method_df[method_df["n"] == 100]
        if n100_df.empty:
            n100_status = "Not executed"
        else:
            n100_status = "/".join(n100_df["status"].unique())
            
        success_count = len(success_df)
        timeout_count = len(method_df[method_df["status"] == "TIMEOUT"])
        blocked_count = len(method_df[method_df["status"] == "BLOCKED_LICENSE"])
        
        if pd.notna(largest_sat_n):
            median_runtime_largest = success_df[success_df["n"] == largest_sat_n]["pipeline_total_time"].median()
        else:
            median_runtime_largest = pd.NA
            
        notes = "License limit" if blocked_count > 0 else ""
        
        rows.append({
            "Method": METHOD_LABELS.get(method, method),
            "Largest SAT+Valid N": largest_sat_n,
            "N=100 Status": n100_status,
            "Success Count": success_count,
            "Timeout Count": timeout_count,
            "Blocked Count": blocked_count,
            "Median Runtime at Largest SAT N": median_runtime_largest,
            "Notes": notes
        })
        
    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "table02_exact_solver_summary.csv", index=False)


def _export_table3_n20(df: pd.DataFrame, output_dir: Path) -> None:
    n_val = 20
    rows = []
    
    for method in METHOD_LABELS.keys():
        method_df = df[(df["method_id"] == method) & (df["n"] == n_val)]
        if method_df.empty:
            continue
            
        success_df = method_df[(method_df["status"] == "SAT") & (method_df["valid"] == True)]
        success_runs = len(success_df)
        
        median_t = success_df["pipeline_total_time"].median() if not success_df.empty else pd.NA
        mean_t = success_df["pipeline_total_time"].mean() if not success_df.empty else pd.NA
        std_t = success_df["pipeline_total_time"].std() if not success_df.empty else pd.NA
        
        family = method_df["method_family"].iloc[0] if "method_family" in method_df.columns else "Unknown"
        
        rows.append({
            "Method": METHOD_LABELS.get(method, method),
            "Family": family,
            "Successful Runs": success_runs,
            "Median Runtime": median_t,
            "Mean Runtime": mean_t,
            "Std Runtime": std_t
        })
        
    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "table03_all_methods_n20.csv", index=False)


def _export_table4_cnf_n100(df: pd.DataFrame, output_dir: Path) -> None:
    n_val = 100
    sat_methods = ["sat_pairwise", "sat_binary", "sat_sequential", "sat_commander", "sat_product"]
    rows = []
    
    for method in sat_methods:
        method_df = df[(df["method_id"] == method) & (df["n"] == n_val)]
        if method_df.empty:
            continue
            
        p_var = method_df["primary_variables"].max()
        a_var = method_df["auxiliary_variables"].max()
        clauses = method_df["clauses"].max()
        
        rows.append({
            "Encoding": METHOD_LABELS.get(method, method),
            "Primary Variables": p_var,
            "Auxiliary Variables": a_var,
            "Total Variables": p_var + a_var if pd.notna(p_var) and pd.notna(a_var) else pd.NA,
            "Clauses": clauses
        })
        
    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "table04_sat_structure_n100.csv", index=False)


def _export_table5_completion(df: pd.DataFrame, output_dir: Path) -> None:
    rows = []
    for method in METHOD_LABELS.keys():
        for n_val in sorted(df["n"].unique()):
            method_df = df[(df["method_id"] == method) & (df["n"] == n_val)]
            if method_df.empty:
                continue
                
            planned = len(method_df)
            success = len(method_df[(method_df["status"] == "SAT") & (method_df["valid"] == True)])
            timeout = len(method_df[method_df["status"] == "TIMEOUT"])
            blocked = len(method_df[method_df["status"] == "BLOCKED_LICENSE"])
            error = len(method_df[~method_df["status"].isin(["SAT", "TIMEOUT", "BLOCKED_LICENSE"])])
            
            rows.append({
                "Method": METHOD_LABELS.get(method, method),
                "N": n_val,
                "Planned Runs": planned,
                "Successful Runs": success,
                "Timeout Runs": timeout,
                "License Blocked Runs": blocked,
                "Error Runs": error
            })
            
    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "table05_completion_status.csv", index=False)


def _export_table6_setup(metadata: Dict[str, Any], output_dir: Path) -> None:
    # Just flatten some key properties
    rows = []
    
    if metadata:
        sys_env = metadata.get("system_environment", {})
        config = metadata.get("experiment_config", {})
        
        properties = {
            "CPU": sys_env.get("cpu_info", "Unknown"),
            "RAM": sys_env.get("ram_gb", "Unknown"),
            "OS": f"{sys_env.get('os_system', '')} {sys_env.get('os_release', '')}",
            "Python Version": sys_env.get("python_version", "Unknown"),
            "Worker Count": config.get("workers", "Unknown"),
            "Time Limit": config.get("timeout", "Unknown"),
            "Repetitions": config.get("repetitions", "Unknown"),
            "SAT Phase Policy": config.get("sat_phase_policy", "Unknown")
        }
        
        for k, v in properties.items():
            rows.append({"Parameter": k, "Value": v})
            
    if not rows:
        rows.append({"Parameter": "Metadata", "Value": "Not available"})
        
    pd.DataFrame(rows).to_csv(output_dir / "table06_experiment_configuration.csv", index=False)
