import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from .plot_config import (
    apply_scientific_style,
    EXACT_METHODS,
    METHOD_COLORS,
    METHOD_MARKERS,
    METHOD_LABELS,
)

def plot_exact_solver_runtime_vs_n(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    plt.figure(figsize=(8, 6))
    
    for method in EXACT_METHODS:
        method_df = df[(df["method_id"] == method) & (df["status"] == "SAT") & (df["valid"] == True)]
        if method_df.empty:
            continue
            
        agg_df = method_df.groupby("n")["pipeline_total_time"].median().reset_index()
        agg_df = agg_df.sort_values("n")
        
        plt.plot(
            agg_df["n"], 
            agg_df["pipeline_total_time"], 
            marker=METHOD_MARKERS.get(method, "o"), 
            color=METHOD_COLORS.get(method, "k"), 
            label=METHOD_LABELS.get(method, method),
            linewidth=2,
            markersize=6
        )

    # Note about license limits for Gurobi and CPLEX MIP
    # We find if there are any BLOCKED_LICENSE runs for them to place a note
    blocked_df = df[df["status"] == "BLOCKED_LICENSE"]
    if not blocked_df.empty:
        gurobi_blocked = blocked_df[blocked_df["method_id"] == "gurobi_mip"]["n"].min()
        cplex_blocked = blocked_df[blocked_df["method_id"] == "cplex_mip"]["n"].min()
        
        notes = []
        if pd.notna(gurobi_blocked):
            notes.append(f"Gurobi: N >= {int(gurobi_blocked)} blocked by license")
        if pd.notna(cplex_blocked):
            notes.append(f"CPLEX MIP: N >= {int(cplex_blocked)} blocked by license")
            
        if notes:
            plt.text(0.05, 0.95, "\n".join(notes), transform=plt.gca().transAxes, 
                     fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.xlabel("N — Board size")
    plt.ylabel("Median pipeline total time (seconds)")
    plt.title("Figure 2: Exact Solver Runtime vs N")
    
    plt.yscale("log")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend()
    
    plt.savefig(output_dir / "fig02_exact_solver_runtime_vs_n.png")
    plt.savefig(output_dir / "fig02_exact_solver_runtime_vs_n.pdf")
    plt.close()
