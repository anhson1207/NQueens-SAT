import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from .plot_config import apply_scientific_style, METHOD_COLORS, METHOD_LABELS

def plot_runtime_variability(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    target_ns = [20, 32, 50, 100]
    
    # Filter to successful runs
    success_df = df[(df["n"].isin(target_ns)) & (df["status"] == "SAT") & (df["valid"] == True)].copy()
    if success_df.empty:
        return
        
    success_df["method_label"] = success_df["method_id"].map(lambda x: METHOD_LABELS.get(x, x))
    
    # We want a grouped dot plot or boxplot. A categorical strip plot (dot plot) per N is good.
    # Since runtimes can vary wildly across N, we might want separate subplots per N or a log scale.
    # We will use subplots per N.
    
    present_ns = sorted(success_df["n"].unique())
    n_plots = len(present_ns)
    
    fig, axes = plt.subplots(1, n_plots, figsize=(4 * n_plots, 6), sharey=False)
    if n_plots == 1:
        axes = [axes]
        
    for ax, n_val in zip(axes, present_ns):
        n_df = success_df[success_df["n"] == n_val]
        
        # Sort methods by median runtime
        order = n_df.groupby("method_label")["pipeline_total_time"].median().sort_values().index
        
        # Use a swarmplot or stripplot
        sns.stripplot(
            data=n_df, 
            x="method_label", 
            y="pipeline_total_time", 
            order=order, 
            ax=ax, 
            palette=[METHOD_COLORS.get({v:k for k,v in METHOD_LABELS.items()}.get(m, m), "k") for m in order],
            jitter=0.1, 
            size=6,
            alpha=0.8
        )
        
        ax.set_title(f"N = {n_val}")
        ax.set_ylabel("Runtime (seconds)" if ax == axes[0] else "")
        ax.set_xlabel("")
        ax.tick_params(axis='x', rotation=45)
        
        # Format y axis
        ax.set_yscale('log')
        ax.grid(True, axis='y', ls="--", alpha=0.5)
        
        # Make x labels wrap or align right
        for label in ax.get_xticklabels():
            label.set_ha('right')
            
    plt.suptitle("Figure 7: Runtime Variability Across Repetitions", y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / "fig07_runtime_variability.png")
    plt.savefig(output_dir / "fig07_runtime_variability.pdf")
    plt.close()
