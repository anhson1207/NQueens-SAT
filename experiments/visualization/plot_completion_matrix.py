import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from .plot_config import apply_scientific_style, METHOD_LABELS

def plot_completion_matrix(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    all_methods = list(METHOD_LABELS.keys())
    n_values = sorted(df["n"].unique())
    if not n_values:
        return
        
    matrix_text = np.empty((len(all_methods), len(n_values)), dtype=object)
    matrix_color = np.zeros((len(all_methods), len(n_values)))
    
    for i, method in enumerate(all_methods):
        for j, n_val in enumerate(n_values):
            cell_df = df[(df["method_id"] == method) & (df["n"] == n_val)]
            if cell_df.empty:
                matrix_text[i, j] = "N/A"
                matrix_color[i, j] = 0 # Gray out or neutral
                continue
                
            total = len(cell_df)
            sat_count = len(cell_df[cell_df["status"] == "SAT"])
            timeout_count = len(cell_df[cell_df["status"] == "TIMEOUT"])
            blocked_count = len(cell_df[cell_df["status"] == "BLOCKED_LICENSE"])
            err_count = len(cell_df[~cell_df["status"].isin(["SAT", "TIMEOUT", "BLOCKED_LICENSE"])])
            
            if blocked_count == total and total > 0:
                matrix_text[i, j] = "LIC"
                matrix_color[i, j] = 1 # Blocked
            elif err_count > 0:
                matrix_text[i, j] = "ERR"
                matrix_color[i, j] = 2 # Error
            elif timeout_count == total and total > 0:
                matrix_text[i, j] = "T/O"
                matrix_color[i, j] = 3 # Timeout completely
            elif sat_count == total and total > 0:
                matrix_text[i, j] = f"{sat_count}/{total}"
                matrix_color[i, j] = 5 # All success
            else:
                matrix_text[i, j] = f"{sat_count}/{total}"
                matrix_color[i, j] = 4 # Partial success
                
    fig, ax = plt.subplots(figsize=(max(8, len(n_values)*0.6), max(4, len(all_methods)*0.4)))
    
    # Custom color map
    # 0: NA (grey), 1: LIC (blueish), 2: ERR (red), 3: T/O (orange), 4: Partial (yellow), 5: All SAT (green)
    cmap = plt.matplotlib.colors.ListedColormap(['#d3d3d3', '#1f77b4', '#d62728', '#ff7f0e', '#bcbd22', '#2ca02c'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = plt.matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    
    cax = ax.matshow(matrix_color, cmap=cmap, norm=norm)
    
    for i in range(len(all_methods)):
        for j in range(len(n_values)):
            text_color = "white" if matrix_color[i, j] in [1, 2] else "black"
            ax.text(j, i, matrix_text[i, j], ha="center", va="center", color=text_color, fontsize=9)
            
    ax.set_xticks(range(len(n_values)))
    ax.set_yticks(range(len(all_methods)))
    ax.set_xticklabels([str(int(n)) for n in n_values])
    ax.set_yticklabels([METHOD_LABELS.get(m, m) for m in all_methods])
    
    ax.xaxis.set_ticks_position('bottom')
    plt.xlabel("N — Board size")
    plt.title("Figure 6: Completion / Timeout Matrix", pad=20)
    
    # Custom legend
    import matplotlib.patches as mpatches
    legend_elements = [
        mpatches.Patch(color='#2ca02c', label='All Successful'),
        mpatches.Patch(color='#bcbd22', label='Partial Success'),
        mpatches.Patch(color='#ff7f0e', label='All Timeout'),
        mpatches.Patch(color='#1f77b4', label='Blocked by License'),
        mpatches.Patch(color='#d62728', label='Error'),
        mpatches.Patch(color='#d3d3d3', label='Not Executed')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
    
    plt.tight_layout()
    plt.savefig(output_dir / "fig06_completion_matrix.png")
    plt.savefig(output_dir / "fig06_completion_matrix.pdf")
    plt.close()
