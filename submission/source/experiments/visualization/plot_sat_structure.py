import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from .plot_config import apply_scientific_style, METHOD_COLORS, METHOD_MARKERS, METHOD_LABELS, SAT_METHODS

def plot_sat_clause_growth(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    plt.figure(figsize=(8, 6))
    
    for method in SAT_METHODS:
        method_df = df[(df["method_id"] == method) & (df["clauses"].notna())]
        if method_df.empty:
            continue
            
        agg_df = method_df.groupby("n")["clauses"].max().reset_index()
        agg_df = agg_df.sort_values("n")
        
        plt.plot(
            agg_df["n"], 
            agg_df["clauses"], 
            marker=METHOD_MARKERS.get(method, "o"), 
            color=METHOD_COLORS.get(method, "k"), 
            label=METHOD_LABELS.get(method, method),
            linewidth=2,
            markersize=6
        )

    plt.xlabel("N — Board size")
    plt.ylabel("Number of CNF clauses")
    plt.title("Figure 4: CNF Clause Growth vs N")
    
    plt.yscale("log")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend()
    
    plt.savefig(output_dir / "fig04_sat_clause_growth.png")
    plt.savefig(output_dir / "fig04_sat_clause_growth.pdf")
    plt.close()

def plot_sat_variable_overhead_n100(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    n_val = 100
    labels = []
    primary_vars = []
    aux_vars = []
    
    for method in SAT_METHODS:
        method_df = df[(df["n"] == n_val) & (df["method_id"] == method) & (df["primary_variables"].notna())]
        if method_df.empty:
            continue
            
        p_var = method_df["primary_variables"].max()
        a_var = method_df["auxiliary_variables"].max()
        
        labels.append(METHOD_LABELS.get(method, method))
        primary_vars.append(p_var)
        aux_vars.append(a_var)
        
    if not labels:
        return
        
    x = np.arange(len(labels))
    width = 0.6
    
    plt.figure(figsize=(8, 6))
    
    p1 = plt.bar(x, primary_vars, width, label='Primary Variables', color='#1f77b4', edgecolor='black')
    p2 = plt.bar(x, aux_vars, width, bottom=primary_vars, label='Auxiliary Variables', color='#ff7f0e', edgecolor='black')
    
    plt.ylabel("Number of Variables")
    plt.title(f"Figure 5: SAT Variable Overhead at N={n_val}")
    plt.xticks(x, labels, rotation=15, ha='right')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / "fig05_sat_variable_overhead_n100.png")
    plt.savefig(output_dir / "fig05_sat_variable_overhead_n100.pdf")
    plt.close()
