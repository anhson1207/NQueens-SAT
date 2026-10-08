import argparse
import json
import csv
import hashlib
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
CONFIG_FINGERPRINT_VERSION = 1
CONFIG_FINGERPRINT_FIELDS = (
    "experiment_id",
    "mode",
    "n_values",
    "repeats",
    "methods",
    "timeout",
    "external_timeout",
    "sat_phase_policy",
    "workers",
    "random_seed",
    "schedule_seed",
)

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


def configuration_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return the result-affecting configuration in a stable JSON shape."""
    missing = [field for field in CONFIG_FINGERPRINT_FIELDS if field not in config]
    if missing:
        raise ValueError(f"Configuration is missing fingerprint fields: {missing}")
    return {
        "fingerprint_version": CONFIG_FINGERPRINT_VERSION,
        **{field: config[field] for field in CONFIG_FINGERPRINT_FIELDS},
        "gurobi_max_n": GUROBI_MAX_N,
        "cplex_mip_max_n": CPLEX_MIP_MAX_N,
        "warmup_n": 4,
        "warmup_repetitions": 1,
    }


def compute_config_fingerprint(config: Dict[str, Any]) -> str:
    """Hash the canonical result-affecting experiment configuration."""
    encoded = json.dumps(
        configuration_payload(config), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def official_trial_key(record: Dict[str, Any]) -> tuple[str, int, int]:
    """Return the logical identity of one official trial."""
    return (record.get("method_id"), record.get("n"), record.get("repetition"))


def _expected_run_id(config: Dict[str, Any], trial: Dict[str, Any]) -> str:
    return (
        f"{config['experiment_id']}_{trial['method_id']}_"
        f"n{trial['n']}_r{trial['repetition']}"
    )


def _validate_record_configuration(
    record: Dict[str, Any],
    trial: Dict[str, Any],
    schedule_index: int,
    config: Dict[str, Any],
    fingerprint: str,
) -> List[str]:
    """Validate record-level evidence without rewriting legacy records."""
    problems: List[str] = []
    run_id = record.get("run_id")
    expected_run_id = _expected_run_id(config, trial)
    if record.get("experiment_id") != config["experiment_id"]:
        problems.append(
            f"{run_id}: experiment_id={record.get('experiment_id')!r}, "
            f"expected {config['experiment_id']!r}"
        )
    if run_id != expected_run_id:
        problems.append(f"{run_id}: expected run_id {expected_run_id}")
    if record.get("schedule_index") != schedule_index:
        problems.append(
            f"{run_id}: schedule_index={record.get('schedule_index')!r}, "
            f"expected {schedule_index}"
        )
    for field, expected in (
        ("workers", config["workers"]),
        ("random_seed", config["random_seed"]),
        ("internal_timeout", config["timeout"]),
        ("external_timeout", config["external_timeout"]),
    ):
        if record.get(field) != expected:
            problems.append(
                f"{run_id}: {field}={record.get(field)!r}, expected {expected!r}"
            )

    method_id = trial["method_id"]
    if REGISTRY[method_id]["method_family"] == "SAT":
        if record.get("phase_policy") != config["sat_phase_policy"]:
            problems.append(
                f"{run_id}: phase_policy={record.get('phase_policy')!r}, "
                f"expected {config['sat_phase_policy']!r}"
            )
    elif record.get("phase_policy") is not None:
        problems.append(f"{run_id}: non-SAT record has a phase policy")

    stored_fingerprint = record.get("config_fingerprint")
    if stored_fingerprint is not None and stored_fingerprint != fingerprint:
        problems.append(
            f"{run_id}: config_fingerprint={stored_fingerprint}, expected {fingerprint}"
        )

    if record.get("status") == "SAT" and record.get("valid") is not True:
        problems.append(f"{run_id}: SAT record is not valid=True")

    blocked_by_policy = (
        (method_id == "gurobi_mip" and trial["n"] > GUROBI_MAX_N)
        or (method_id == "cplex_mip" and trial["n"] > CPLEX_MIP_MAX_N)
    )
    if record.get("status") == "BLOCKED_LICENSE":
        if not blocked_by_policy:
            problems.append(f"{run_id}: unexpected BLOCKED_LICENSE for this method/N")
        if record.get("executed") is not False:
            problems.append(f"{run_id}: BLOCKED_LICENSE record must have executed=False")
        if record.get("pipeline_total_time") is not None:
            problems.append(f"{run_id}: BLOCKED_LICENSE has pipeline_total_time")
    elif blocked_by_policy:
        problems.append(f"{run_id}: expected proactive BLOCKED_LICENSE")

    if record.get("executed"):
        expected_command = build_cli_command(method_id, trial["n"], config)
        command = record.get("command")
        if not isinstance(command, list) or command[1:] != expected_command[1:]:
            problems.append(f"{run_id}: command does not match current configuration")
    return problems


def load_and_validate_resume_state(
    raw_jsonl_path: Path,
    schedule: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Load a raw JSONL file and reject unsafe or ambiguous resume states."""
    fingerprint = compute_config_fingerprint(config)
    schedule_by_run_id: Dict[str, tuple[int, Dict[str, Any]]] = {}
    expected_official_keys = set()
    for index, trial in enumerate(schedule):
        run_id = _expected_run_id(config, trial)
        schedule_by_run_id[run_id] = (index, trial)
        if not trial["is_warmup"]:
            expected_official_keys.add(
                (trial["method_id"], trial["n"], trial["repetition"])
            )

    official_records: List[Dict[str, Any]] = []
    completed_run_ids: Dict[str, Dict[str, Any]] = {}
    completed_keys = set()
    completed_warmup_methods = set()
    seen_official_run_ids = set()
    legacy_without_fingerprint = 0
    warmup_records = 0
    warmup_duplicate_records = 0
    problems: List[str] = []

    with raw_jsonl_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Malformed JSON in {raw_jsonl_path} at line {line_number}: {exc}"
                ) from exc
            if not isinstance(record, dict):
                problems.append(f"Line {line_number}: record is not a JSON object")
                continue

            run_id = record.get("run_id")
            scheduled = schedule_by_run_id.get(run_id)
            if scheduled is None:
                problems.append(f"Line {line_number}: unexpected run_id {run_id!r}")
                continue
            schedule_index, trial = scheduled
            is_warmup = record.get("is_warmup", False)
            if is_warmup != trial["is_warmup"]:
                problems.append(
                    f"Line {line_number}: warm-up flag does not match schedule for {run_id}"
                )
                continue

            record_problems = _validate_record_configuration(
                record, trial, schedule_index, config, fingerprint
            )
            problems.extend(f"Line {line_number}: {problem}" for problem in record_problems)

            if is_warmup:
                warmup_records += 1
                method_id = record.get("method_id")
                if method_id in completed_warmup_methods:
                    warmup_duplicate_records += 1
                completed_warmup_methods.add(method_id)
                continue

            key = official_trial_key(record)
            if run_id in seen_official_run_ids:
                problems.append(f"Line {line_number}: duplicate official run_id {run_id}")
            if key in completed_keys:
                problems.append(f"Line {line_number}: duplicate official trial key {key}")
            if key not in expected_official_keys:
                problems.append(f"Line {line_number}: unexpected official trial key {key}")
            seen_official_run_ids.add(run_id)
            completed_keys.add(key)
            completed_run_ids[run_id] = record
            official_records.append(record)
            if record.get("config_fingerprint") is None:
                legacy_without_fingerprint += 1

    if problems:
        preview = "\n".join(f"- {problem}" for problem in problems[:25])
        remainder = len(problems) - 25
        if remainder > 0:
            preview += f"\n- ... and {remainder} more problem(s)"
        raise ValueError(f"Resume integrity validation failed:\n{preview}")

    return {
        "config_fingerprint": fingerprint,
        "official_records": official_records,
        "completed_run_ids": completed_run_ids,
        "completed_keys": completed_keys,
        "completed_warmup_methods": completed_warmup_methods,
        "expected_official_keys": expected_official_keys,
        "missing_keys": expected_official_keys - completed_keys,
        "legacy_records_without_fingerprint": legacy_without_fingerprint,
        "warmup_records": warmup_records,
        "warmup_duplicate_records": warmup_duplicate_records,
    }


def write_config_sidecar(
    path: Path, config: Dict[str, Any], resume_state: Dict[str, Any]
) -> None:
    """Atomically persist the verified configuration for future resumes."""
    payload = {
        "config_fingerprint": resume_state["config_fingerprint"],
        "fingerprint_payload": configuration_payload(config),
        "legacy_records_without_fingerprint": resume_state[
            "legacy_records_without_fingerprint"
        ],
        "legacy_provenance_note": (
            "Historical records were not modified or assigned a retrospective "
            "fingerprint. They were accepted only after record-level compatibility "
            "checks against the recovery configuration."
        ),
    }
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("config_fingerprint") != payload["config_fingerprint"]:
            raise ValueError(
                f"Configuration sidecar mismatch: {path} belongs to a different run"
            )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

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
    record["config_fingerprint"] = config.get("config_fingerprint")
    
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
    config["config_fingerprint"] = compute_config_fingerprint(config)
    
    out_dir_raw = Path("results/raw")
    out_dir_proc = Path("results/processed")
    out_dir_meta = Path("results/metadata")
    for d in [out_dir_raw, out_dir_proc, out_dir_meta]:
        d.mkdir(parents=True, exist_ok=True)
        
    raw_jsonl_path = out_dir_raw / f"benchmark_{experiment_id}.jsonl"
    proc_csv_path = out_dir_proc / f"benchmark_{experiment_id}.csv"
    summary_csv_path = out_dir_proc / f"benchmark_summary_{experiment_id}.csv"
    meta_json_path = out_dir_meta / f"benchmark_{experiment_id}_metadata.json"
    config_json_path = out_dir_meta / f"benchmark_{experiment_id}_config.json"
    
    schedule = generate_schedule(n_values, args.methods, repeats, args.schedule_seed)
    
    completed_runs: Dict[str, Dict[str, Any]] = {}
    completed_keys = set()
    completed_warmup_methods = set()
    records: List[Dict[str, Any]] = []
    resume_state = {
        "config_fingerprint": config["config_fingerprint"],
        "legacy_records_without_fingerprint": 0,
    }
    
    if args.resume and raw_jsonl_path.exists():
        resume_state = load_and_validate_resume_state(raw_jsonl_path, schedule, config)
        completed_runs = resume_state["completed_run_ids"]
        completed_keys = resume_state["completed_keys"]
        completed_warmup_methods = resume_state["completed_warmup_methods"]
        records = list(resume_state["official_records"])
        print(
            f"Resuming experiment '{experiment_id}'. Found "
            f"{len(completed_runs)} compatible official trials; "
            f"{len(resume_state['missing_keys'])} remain."
        )
        if resume_state["legacy_records_without_fingerprint"]:
            print(
                "Validated "
                f"{resume_state['legacy_records_without_fingerprint']} legacy records "
                "from record-level configuration evidence; raw history was not modified."
            )
        if resume_state["warmup_duplicate_records"]:
            print(
                "Preserving "
                f"{resume_state['warmup_duplicate_records']} historical duplicate warm-up "
                "records; no new duplicate warm-ups will be written."
            )
    else:
        # Create or overwrite file
        if raw_jsonl_path.exists():
            if not args.resume:
                print(f"Warning: Overwriting {raw_jsonl_path}")
        with open(raw_jsonl_path, "w", encoding="utf-8") as f:
            pass

    write_config_sidecar(config_json_path, config, resume_state)
            
    with open(raw_jsonl_path, "a", encoding="utf-8") as f_jsonl:
        for idx, trial in enumerate(schedule):
            is_warmup = trial["is_warmup"]
            run_id = f"{experiment_id}_{trial['method_id']}_n{trial['n']}_r{trial['repetition']}"

            if is_warmup and trial["method_id"] in completed_warmup_methods:
                continue
            if not is_warmup and (
                run_id in completed_runs
                or (trial["method_id"], trial["n"], trial["repetition"])
                in completed_keys
            ):
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
                completed_runs[run_id] = record
                completed_keys.add(
                    (trial["method_id"], trial["n"], trial["repetition"])
                )
            else:
                completed_warmup_methods.add(trial["method_id"])
                
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
        "methods_included": args.methods,
        "config_fingerprint": config["config_fingerprint"],
        "fingerprint_version": CONFIG_FINGERPRINT_VERSION,
        "experiment_config": configuration_payload(config),
        "legacy_records_without_fingerprint": resume_state[
            "legacy_records_without_fingerprint"
        ],
    })
    
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"Artifacts saved to:\n  {raw_jsonl_path}\n  {proc_csv_path}\n  {summary_csv_path}\n  {meta_json_path}")

if __name__ == "__main__":
    main()
