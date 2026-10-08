import csv
import json
from collections import defaultdict
import statistics
from typing import List, Dict, Any, Optional

def compute_statistics(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute basic statistics grouped by method_id and N."""
    groups = defaultdict(list)
    for record in records:
        key = (record["method_id"], record["n"])
        groups[key].append(record)
        
    summaries = []
    for (method_id, n), group_records in groups.items():
        runs_planned = len(group_records) # Since records contains one per planned trial
        executed_runs = [r for r in group_records if r.get("executed")]
        successful_runs = [r for r in executed_runs if r.get("status") == "SAT" and r.get("valid") is True]
        
        runs_executed_count = len(executed_runs)
        successful_count = len(successful_runs)
        timeout_count = sum(1 for r in executed_runs if r.get("status") == "TIMEOUT")
        license_blocked_count = sum(1 for r in group_records if r.get("status") == "BLOCKED_LICENSE" or r.get("status") == "LICENSE_ERROR")
        error_count = sum(1 for r in executed_runs if r.get("status") == "ERROR")
        
        success_rate = successful_count / runs_executed_count if runs_executed_count > 0 else 0.0
        
        times = [r["pipeline_total_time"] for r in successful_runs if r.get("pipeline_total_time") is not None]
        
        mean_time = statistics.mean(times) if times else None
        median_time = statistics.median(times) if times else None
        min_time = min(times) if times else None
        max_time = max(times) if times else None
        
        if len(times) > 1:
            std_time = statistics.stdev(times)
        else:
            std_time = None
            
        summaries.append({
            "method_id": method_id,
            "n": n,
            "runs_planned": runs_planned,
            "runs_executed": runs_executed_count,
            "successful_runs": successful_count,
            "timeout_runs": timeout_count,
            "license_blocked_runs": license_blocked_count,
            "error_runs": error_count,
            "success_rate": success_rate,
            "mean_time": mean_time,
            "median_time": median_time,
            "std_time": std_time,
            "min_time": min_time,
            "max_time": max_time,
        })
        
    # Sort summaries by N then method_id
    summaries.sort(key=lambda x: (x["n"], x["method_id"]))
    return summaries

def export_summary_csv(summaries: List[Dict[str, Any]], filepath: str):
    fieldnames = [
        "method_id", "n", "runs_planned", "runs_executed", 
        "successful_runs", "timeout_runs", "license_blocked_runs", "error_runs", 
        "success_rate", "mean_time", "median_time", "std_time", "min_time", "max_time"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summaries:
            # Format floats for readability if desired, or dump raw
            writer.writerow(row)

