import argparse
import json
import csv
import subprocess
import time
import datetime
import random
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from experiments.solver_registry import METHODS, REGISTRY, build_cli_command
from experiments.environment_info import get_full_environment_metadata
from experiments.benchmark_statistics import compute_statistics, export_summary_csv

# Expected max sizes for current licenses
GUROBI_MAX_N = 44
CPLEX_MIP_MAX_N = 31

def generate_schedule(n_values: List[int], methods: List[str], repeats: int, seed: int) -> List[Dict[str, Any]]:
    """Generate a deterministic schedule of trials."""
    rng = random.Random(seed)
    schedule = []
    
    # Warm-up phase (N=4, 1 repeat)
    for method in methods:
        schedule.append({
            "is_warmup": True,
            "n": 4,
            "method_id": method,
            "repetition": 0
        })
        
    # Official phase
    for r in range(1, repeats + 1):
        for n in n_values:
            # Shuffle methods for each (repetition, N) block to reduce bias
            block_methods = list(methods)
            rng.shuffle(block_methods)
            for method in block_methods:
                schedule.append({
                    "is_warmup": False,
                    "n": n,
                    "method_id": method,
                    "repetition": r
                })
                
    return schedule

def parse_stdout_json(stdout_str: str) -> Optional[Dict[str, Any]]:
    # Sometimes solvers might print warning lines before JSON
    for line in reversed(stdout_str.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None

def execute_trial(trial: Dict[str, Any], config: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    method_id = trial["method_id"]
    n = trial["n"]
    meta = REGISTRY[method_id]
    
    # Base record
    record = {
        "experiment_id": config["experiment_id"],
        "run_id": run_id,
        "method_id": method_id,
        "method_family": meta["method_family"],
        "solver_name": meta["solver_name"],
        "n": n,
        "repetition": trial["repetition"],
        "executed": False,
        "status": "UNKNOWN",
        "native_status": None,
        "has_solution": None,
        "valid": None,
        "queen_count": None,
        "phase_policy": config.get("sat_phase_policy") if meta["method_family"] == "SAT" else None,
        "workers": config.get("workers", meta["default_workers"]),
        "random_seed": config.get("random_seed"),
        "internal_timeout": config.get("timeout"),
        "external_timeout": config.get("external_timeout"),
        "pipeline_total_time": None,
        "process_wall_time": None,
        "encoding_time": None,
        "load_time": None,
        "search_time": None,
        "solve_time": None,
        "build_time": None,
        "decode_validate_time": None,
        "primary_variables": None,
        "auxiliary_variables": None,
        "total_variables": None,
        "clauses": None,
        "linear_constraints": None,
        "statistics": {},
        "error_category": None,
        "error_message": None,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": []
    }
    
    # Check License Skip
    if method_id == "gurobi_mip" and n > GUROBI_MAX_N:
        record["status"] = "BLOCKED_LICENSE"
        record["error_message"] = f"VERIFIED_SIZE_LIMIT (> {GUROBI_MAX_N})"
        return record
        
    if method_id == "cplex_mip" and n > CPLEX_MIP_MAX_N:
        record["status"] = "BLOCKED_LICENSE"
        record["error_message"] = f"VERIFIED_SIZE_LIMIT (> {CPLEX_MIP_MAX_N})"
        return record
        
    cmd = build_cli_command(method_id, n, config)
    record["command"] = cmd
    record["executed"] = True
    
    start_time = time.perf_counter()
    process = None
    try:
        # Create a modified environment with .venv/bin in PATH to find cpoptimizer
        env = os.environ.copy()
        venv_bin = str(Path(".venv/bin").absolute())
        env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config["external_timeout"],
            env=env
        )
        end_time = time.perf_counter()
        record["process_wall_time"] = end_time - start_time
        
        parsed = parse_stdout_json(process.stdout)
        if parsed:
            # Extract fields
            record["status"] = parsed.get("status", "UNKNOWN")
            record["native_status"] = parsed.get("native_status")
            record["has_solution"] = parsed.get("has_solution")
            record["valid"] = parsed.get("valid")
            
            positions = parsed.get("positions")
            record["queen_count"] = len(positions) if positions is not None else None
            
            record["pipeline_total_time"] = parsed.get("total_time")
            record["encoding_time"] = parsed.get("encoding_time")
            record["load_time"] = parsed.get("load_time")
            record["search_time"] = parsed.get("search_time")
            record["solve_time"] = parsed.get("solve_time")
            record["build_time"] = parsed.get("build_time")
            record["decode_validate_time"] = parsed.get("decode_validate_time")
            
            record["primary_variables"] = parsed.get("primary_variables")
            record["auxiliary_variables"] = parsed.get("auxiliary_variables")
            record["total_variables"] = parsed.get("total_variables")
            record["clauses"] = parsed.get("clauses")
            record["linear_constraints"] = parsed.get("linear_constraints")
            
            record["statistics"] = parsed.get("statistics", {})
            record["error_message"] = parsed.get("error")
            
            if record["status"] == "SAT" and record["valid"] is False:
                record["status"] = "VALIDATION_ERROR"
                
            if process.returncode != 0 and record["status"] not in ("LICENSE_ERROR", "TIMEOUT", "VALIDATION_ERROR"):
                record["error_category"] = "NONZERO_EXIT"
        else:
            record["status"] = "ERROR"
            record["error_category"] = "JSON_PARSE_ERROR"
            record["error_message"] = process.stderr.strip()[-500:] if process.stderr else "No JSON and no stderr"
            
    except subprocess.TimeoutExpired:
        end_time = time.perf_counter()
        record["process_wall_time"] = end_time - start_time
        record["status"] = "TIMEOUT"
        record["error_category"] = "EXTERNAL_TIMEOUT"
        
    except Exception as e:
        end_time = time.perf_counter()
        record["process_wall_time"] = end_time - start_time
        record["status"] = "ERROR"
        record["error_category"] = "SUBPROCESS_ERROR"
        record["error_message"] = str(e)
        
    return record

def export_raw_csv(records: List[Dict[str, Any]], filepath: str):
    fieldnames = [
        "experiment_id", "run_id", "method_id", "method_family", "solver_name", 
        "n", "repetition", "status", "native_status", "executed", 
        "has_solution", "valid", "queen_count", "phase_policy", "workers", "random_seed", 
        "pipeline_total_time", "process_wall_time", "encoding_time", "load_time", 
        "search_time", "build_time", "solve_time", "decode_validate_time", 
        "primary_variables", "auxiliary_variables", "total_variables", "clauses", 
        "linear_constraints", "error_category"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            writer.writerow(r)

def parse_args():
    parser = argparse.ArgumentParser(description="Reproducible Benchmark Framework for N-Queens")
    parser.add_argument("--mode", choices=["smoke", "pilot", "full"], default="smoke")
    parser.add_argument("--n", type=int, nargs="+", help="Custom N values")
    parser.add_argument("--repeats", type=int, help="Custom repetition count")
    parser.add_argument("--timeout", type=int, default=300, help="Internal solver time limit")
    parser.add_argument("--external-timeout", type=int, default=330, help="Subprocess external timeout")
    parser.add_argument("--sat-phase-policy", type=str, default="solver_default", choices=["solver_default", "aux_false", "legacy"])
    parser.add_argument("--methods", type=str, nargs="+", default=METHODS, help="Subset of methods to run")
    parser.add_argument("--experiment-id", type=str, help="Experiment identifier")
    parser.add_argument("--schedule-seed", type=int, default=2026, help="Seed for schedule generation")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted experiment")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers/threads")
    parser.add_argument("--random-seed", type=int, default=0, help="Solver random seed")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Mode defaults
    n_values = args.n
    repeats = args.repeats
    if args.mode == "smoke":
        if not n_values: n_values = [4, 8]
        if not repeats: repeats = 1
    elif args.mode == "pilot":
        if not n_values: n_values = [4, 8, 16, 20, 31, 32, 44, 50, 64, 100]
        if not repeats: repeats = 1
    elif args.mode == "full":
        if not n_values: n_values = [4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100]
        if not repeats: repeats = 5
        
    experiment_id = args.experiment_id or f"nqueens_primary_{args.mode}"
    
    config = {
        "experiment_id": experiment_id,
        "mode": args.mode,
        "n_values": n_values,
        "repeats": repeats,
        "methods": args.methods,
        "timeout": args.timeout,
        "external_timeout": args.external_timeout,
        "sat_phase_policy": args.sat_phase_policy,
        "workers": args.workers,
        "random_seed": args.random_seed,
        "schedule_seed": args.schedule_seed,
    }
    
    out_dir_raw = Path("results/raw")
    out_dir_proc = Path("results/processed")
    out_dir_meta = Path("results/metadata")
    for d in [out_dir_raw, out_dir_proc, out_dir_meta]:
        d.mkdir(parents=True, exist_ok=True)
        
    raw_jsonl_path = out_dir_raw / f"benchmark_{experiment_id}.jsonl"
    proc_csv_path = out_dir_proc / f"benchmark_{experiment_id}.csv"
    summary_csv_path = out_dir_proc / f"benchmark_summary_{experiment_id}.csv"
    meta_json_path = out_dir_meta / f"benchmark_{experiment_id}_metadata.json"
    
    schedule = generate_schedule(n_values, args.methods, repeats, args.schedule_seed)
    
    completed_runs = {}
    records = []
    
    if args.resume and raw_jsonl_path.exists():
        with open(raw_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if "run_id" in rec and not rec.get("is_warmup", False):
                            completed_runs[rec["run_id"]] = rec
                            records.append(rec)
                    except json.JSONDecodeError:
                        pass
        print(f"Resuming experiment '{experiment_id}'. Found {len(completed_runs)} completed official trials.")
    else:
        # Create or overwrite file
        if raw_jsonl_path.exists():
            if not args.resume:
                print(f"Warning: Overwriting {raw_jsonl_path}")
        with open(raw_jsonl_path, "w", encoding="utf-8") as f:
            pass
            
    with open(raw_jsonl_path, "a", encoding="utf-8") as f_jsonl:
        for idx, trial in enumerate(schedule):
            is_warmup = trial["is_warmup"]
            run_id = f"{experiment_id}_{trial['method_id']}_n{trial['n']}_r{trial['repetition']}"
            
            if not is_warmup and run_id in completed_runs:
                continue
                
            prefix = "[WARMUP] " if is_warmup else f"[TRIAL {idx+1}/{len(schedule)}] "
            print(f"{prefix}Running {trial['method_id']} (N={trial['n']}, Rep={trial['repetition']})")
            
            record = execute_trial(trial, config, run_id)
            record["is_warmup"] = is_warmup
            record["schedule_index"] = idx
            
            # Print basic result
            print(f"  -> Status: {record['status']}, Total Time: {record['pipeline_total_time']}, Wall Time: {record['process_wall_time']}")
            
            # Write to JSONL
            f_jsonl.write(json.dumps(record) + "\n")
            f_jsonl.flush()
            
            if not is_warmup:
                records.append(record)
                
    print("\nBenchmark completed. Exporting CSVs...")
    
    # Strip warmup records before CSV if they got in
    official_records = [r for r in records if not r.get("is_warmup")]
    
    export_raw_csv(official_records, proc_csv_path)
    
    summaries = compute_statistics(official_records)
    export_summary_csv(summaries, summary_csv_path)
    
    # Save metadata
    meta = get_full_environment_metadata()
    meta.update({
        "experiment_id": experiment_id,
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "experiment_purpose": args.mode,
        "n_values": n_values,
        "repetitions": repeats,
        "schedule_seed": args.schedule_seed,
        "sat_phase_policy": args.sat_phase_policy,
        "time_limit": args.timeout,
        "external_timeout": args.external_timeout,
        "workers": args.workers,
        "random_seed": args.random_seed,
        "methods_included": args.methods
    })
    
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Artifacts saved to:\n  {raw_jsonl_path}\n  {proc_csv_path}\n  {summary_csv_path}\n  {meta_json_path}")

if __name__ == "__main__":
    main()
