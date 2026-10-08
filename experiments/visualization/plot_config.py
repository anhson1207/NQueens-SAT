import matplotlib.pyplot as plt

SAT_METHODS = (
    "sat_pairwise",
    "sat_binary",
    "sat_sequential",
    "sat_commander",
    "sat_product",
)
EXACT_METHODS = ("cp_sat", "gurobi_mip", "cplex_mip", "cplex_cp")

def apply_scientific_style():
    # Use standard fonts that are universally available
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans", "sans-serif"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight"
    })

METHOD_COLORS = {
    "sat_pairwise": "#1f77b4",
    "sat_binary": "#ff7f0e",
    "sat_sequential": "#2ca02c",
    "sat_commander": "#d62728",
    "sat_product": "#9467bd",
    "cp_sat": "#8c564b",
    "gurobi_mip": "#e377c2",
    "cplex_mip": "#7f7f7f",
    "cplex_cp": "#bcbd22"
}

METHOD_MARKERS = {
    "sat_pairwise": "o",
    "sat_binary": "s",
    "sat_sequential": "^",
    "sat_commander": "D",
    "sat_product": "v",
    "cp_sat": "p",
    "gurobi_mip": "*",
    "cplex_mip": "x",
    "cplex_cp": "+"
}

METHOD_LABELS = {
    "sat_pairwise": "SAT-Pairwise",
    "sat_binary": "SAT-Binary",
    "sat_sequential": "SAT-Sequential",
    "sat_commander": "SAT-Commander",
    "sat_product": "SAT-Product",
    "cp_sat": "OR-Tools CP-SAT",
    "gurobi_mip": "Gurobi MIP",
    "cplex_mip": "IBM CPLEX MIP",
    "cplex_cp": "IBM CP Optimizer"
}
