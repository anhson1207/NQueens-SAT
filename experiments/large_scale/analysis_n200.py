import json
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

RAW_N200 = "results/raw/benchmark_nqueens_large_scale_n200.jsonl"
SUMMARY_N100 = "results/processed/benchmark_summary_nqueens_primary_full.csv"
OUT_DIR_TABLES = "results/tables"
OUT_DIR_FIGURES = "results/figures/large_scale_n200"

os.makedirs(OUT_DIR_TABLES, exist_ok=True)
os.makedirs(OUT_DIR_FIGURES, exist_ok=True)

# 1. Load N=200 data
records = []
with open(RAW_N200, "r") as f:
    for line in f:
        records.append(json.loads(line))

df_n200 = pd.DataFrame(records)

# 2. Status counts
status_summary = df_n200.groupby("method_id")["status"].value_counts().unstack(fill_value=0)
all_statuses = ["SAT", "TIMEOUT", "RESOURCE_LIMIT", "BLOCKED_LICENSE", "NOT_RUN_RESOURCE_POLICY", "ERROR", "LICENSE_ERROR"]
for s in all_statuses:
    if s not in status_summary.columns:
        status_summary[s] = 0

status_summary["Successful repetitions"] = status_summary.get("SAT", 0)
status_summary["Timeout repetitions"] = status_summary.get("TIMEOUT", 0)
status_summary["Resource-limited repetitions"] = status_summary.get("RESOURCE_LIMIT", 0)

# 3. Calculate medians for N=200
success_df = df_n200[df_n200["status"] == "SAT"]
medians_n200 = success_df.groupby("method_id")["pipeline_total_time"].median()
means_n200 = success_df.groupby("method_id")["pipeline_total_time"].mean()
stds_n200 = success_df.groupby("method_id")["pipeline_total_time"].std()
peak_memory = df_n200.groupby("method_id")["peak_memory_mb"].max()

method_order = ["sat_binary", "sat_pairwise", "sat_sequential", "sat_commander", "sat_product", "cp_sat", "cplex_cp", "gurobi_mip", "cplex_mip"]
method_names = {
    "sat_binary": "SAT-Binary",
    "sat_pairwise": "SAT-Pairwise",
    "sat_sequential": "SAT-Sequential",
    "sat_commander": "SAT-Commander",
    "sat_product": "SAT-Product",
    "cp_sat": "OR-Tools CP-SAT",
    "cplex_cp": "IBM CP Optimizer",
    "gurobi_mip": "Gurobi MIP",
    "cplex_mip": "IBM CPLEX MIP"
}

# Table 7
table7_data = []
for m in method_order:
    statuses = df_n200[df_n200["method_id"] == m]["status"].unique()
    status_str = ", ".join(statuses) if len(statuses) > 0 else "N/A"
    succ = status_summary.loc[m, "Successful repetitions"] if m in status_summary.index else 0
    if succ > 0:
        med = medians_n200.get(m, np.nan)
        mean_val = means_n200.get(m, np.nan)
        std_val = stds_n200.get(m, np.nan)
    else:
        med, mean_val, std_val = np.nan, np.nan, np.nan
    peak = peak_memory.get(m, np.nan)
    
    table7_data.append({
        "Method": method_names[m],
        "Status": status_str,
        "Success/5": succ,
        "Median Time": med,
        "Mean Time": mean_val,
        "Std Time": std_val,
        "Peak RAM (MB)": peak
    })

df_table7 = pd.DataFrame(table7_data)
df_table7.to_csv(f"{OUT_DIR_TABLES}/table07_large_scale_n200.csv", index=False)

# 4. Compare N=100 and N=200
df_n100_summary = pd.read_csv(SUMMARY_N100)
df_n100 = df_n100_summary[df_n100_summary["n"] == 100].set_index("method_id")

comparison_data = []
for m in method_order:
    m_name = method_names[m]
    if m in df_n100.index:
        med100 = df_n100.loc[m, "median_time"]
        try:
            med100 = float(med100)
        except:
            med100 = np.nan
    else:
        med100 = np.nan
        
    succ_n200 = status_summary.loc[m, "Successful repetitions"] if m in status_summary.index else 0
    med200 = medians_n200.get(m, np.nan)
    
    if pd.isna(med100) or pd.isna(med200):
        ratio = np.nan
    else:
        ratio = med200 / med100
        
    statuses = df_n200[df_n200["method_id"] == m]["status"].unique()
    status_str = ", ".join(statuses) if len(statuses) > 0 else "N/A"
    
    comparison_data.append({
        "Method": m_name,
        "N=100 Median": med100,
        "N=200 Median": med200,
        "Runtime Ratio": ratio,
        "N=200 Status": status_str
    })
df_comparison = pd.DataFrame(comparison_data)
df_comparison.to_csv(f"{OUT_DIR_TABLES}/table08_n100_vs_n200.csv", index=False)

# 5. Figure 8 - Runtime Comparison
plt.figure(figsize=(10, 6))
methods_plot = []
n100_plot = []
n200_plot = []
for row in comparison_data:
    if not pd.isna(row["N=100 Median"]) or not pd.isna(row["N=200 Median"]):
        methods_plot.append(row["Method"])
        n100_plot.append(row["N=100 Median"] if not pd.isna(row["N=100 Median"]) else 0)
        n200_plot.append(row["N=200 Median"] if not pd.isna(row["N=200 Median"]) else 0)

x = np.arange(len(methods_plot))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
rects1 = ax.bar(x - width/2, n100_plot, width, label='N=100')
rects2 = ax.bar(x + width/2, n200_plot, width, label='N=200')

ax.set_ylabel('Median Pipeline Time (s)')
ax.set_title('Runtime Comparison at N=100 and N=200')
ax.set_xticks(x)
ax.set_xticklabels(methods_plot, rotation=45, ha='right')
ax.legend()
plt.yscale('log')
plt.tight_layout()
plt.savefig(f"{OUT_DIR_FIGURES}/fig08_n100_vs_n200.png", dpi=300)
plt.savefig(f"{OUT_DIR_FIGURES}/fig08_n100_vs_n200.pdf")
plt.close()

# 6. Figure 9 - N=200 Completion Status
status_df = status_summary[["SAT", "TIMEOUT", "RESOURCE_LIMIT", "BLOCKED_LICENSE", "NOT_RUN_RESOURCE_POLICY", "LICENSE_ERROR", "ERROR"]].copy()
status_df.index = [method_names.get(i, i) for i in status_df.index]
status_df = status_df.loc[:, (status_df != 0).any(axis=0)]
status_df.plot(kind='bar', stacked=True, figsize=(10, 6))
plt.title('N=200 Completion and Resource Outcomes')
plt.ylabel('Number of Trials')
plt.xlabel('Method')
plt.xticks(rotation=45, ha='right')
plt.legend(title='Status', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(f"{OUT_DIR_FIGURES}/fig09_n200_completion.png", dpi=300)
plt.savefig(f"{OUT_DIR_FIGURES}/fig09_n200_completion.pdf")
plt.close()
