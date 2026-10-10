import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from .plot_config import apply_scientific_style, METHOD_COLORS, METHOD_LABELS

def plot_all_methods_n20(df: pd.DataFrame, output_dir: Path) -> None:
    apply_scientific_style()
    
    n_val = 20
    df_n = df[(df["n"] == n_val) & (df["status"] == "SAT") & (df["valid"] == True)]
    
    if df_n.empty:
        return
        
    agg_df = df_n.groupby("method_id")["pipeline_total_time"].median().reset_index()
    agg_df = agg_df.sort_values("pipeline_total_time")
    
    # We may want to add methods that failed/timeout/blocked for completeness
    # but the instructions say: "Nhóm phương pháp bằng màu hoặc ký hiệu", "Sắp xếp theo median từ thấp đến cao nếu có dữ liệu hợp lệ", "Nếu không giả định tất cả đều chạy thành công; nếu thiếu kết quả, thể hiện riêng nguyên nhân".
    
    methods_present = agg_df["method_id"].tolist()
    all_methods = list(METHOD_LABELS.keys())
    missing = set(all_methods) - set(methods_present)
    
    plt.figure(figsize=(10, 6))
    
    y_pos = range(len(methods_present))
    runtimes = agg_df["pipeline_total_time"].tolist()
    labels = [METHOD_LABELS.get(m, m) for m in methods_present]
    colors = [METHOD_COLORS.get(m, "gray") for m in methods_present]
    
    plt.barh(y_pos, runtimes, color=colors, edgecolor='black')
    
    plt.yticks(y_pos, labels)
    plt.xlabel("Median pipeline total time (seconds)")
    plt.title(f"Figure 3: All-Nine-Method Comparison at N={n_val}")
    
    # Add a note for missing methods
    if missing:
        missing_text = []
        for m in missing:
            m_df = df[(df["n"] == n_val) & (df["method_id"] == m)]
            if m_df.empty:
                missing_text.append(f"{METHOD_LABELS.get(m, m)}: Not executed")
            else:
                statuses = m_df["status"].unique()
                missing_text.append(f"{METHOD_LABELS.get(m, m)}: {', '.join(statuses)}")
        
        plt.text(0.95, 0.05, "Missing/Failed:\n" + "\n".join(missing_text),
                 transform=plt.gca().transAxes, fontsize=9,
                 verticalalignment='bottom', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                 
    plt.grid(True, axis='x', ls="--", alpha=0.5)
    
    plt.savefig(output_dir / f"fig03_all_methods_n{n_val}.png")
    plt.savefig(output_dir / f"fig03_all_methods_n{n_val}.pdf")
    plt.close()
