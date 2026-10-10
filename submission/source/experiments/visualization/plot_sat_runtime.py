import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
from .plot_config import apply_scientific_style, METHOD_COLORS, METHOD_MARKERS, METHOD_LABELS, SAT_METHODS

def plot_sat_runtime_vs_n(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    plt.figure(figsize=(8, 6))
    
    for method in SAT_METHODS:
        method_df = df[(df["method_id"] == method) & (df["status"] == "SAT") & (df["valid"] == True)]
        if method_df.empty:
            continue
            
        # Group by N and compute median pipeline_total_time
        agg_df = method_df.groupby("n")["pipeline_total_time"].median().reset_index()
        agg_df = agg_df.sort_values("n")
        
        # Count successes to annotate or filter if needed
        success_counts = method_df.groupby("n").size()
        
        plt.plot(
            agg_df["n"], 
            agg_df["pipeline_total_time"], 
            marker=METHOD_MARKERS.get(method, "o"), 
            color=METHOD_COLORS.get(method, "k"), 
            label=METHOD_LABELS.get(method, method),
            linewidth=2,
            markersize=6
        )
        
        # Optional: Add annotations for sparse success rates (e.g. 1/5)
        for _, row in agg_df.iterrows():
            n_val = row["n"]
            count = success_counts.get(n_val, 0)
            if count > 0 and count < 5:
                plt.annotate(f"{count}/5", (n_val, row["pipeline_total_time"]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

    plt.xlabel("N — Board size")
    plt.ylabel("Median pipeline total time (seconds)")
    plt.title("Figure 1: SAT Encoding Runtime vs N")
    
    plt.yscale("log")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend()
    
    plt.savefig(output_dir / "fig01_sat_runtime_vs_n.png")
    plt.savefig(output_dir / "fig01_sat_runtime_vs_n.pdf")
    plt.close()
