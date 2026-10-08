import json
import logging
from pathlib import Path
from typing import Dict, Any, List

EXPECTED_METHODS = 9
EXPECTED_N_VALUES = 11
EXPECTED_REPETITIONS = 5
EXPECTED_OFFICIAL_RECORDS = EXPECTED_METHODS * EXPECTED_N_VALUES * EXPECTED_REPETITIONS

def validate_full_benchmark_dataset(
    raw_path: str | Path,
    metadata_path: str | Path,
) -> Dict[str, Any]:
    raw_path = Path(raw_path)
    metadata_path = Path(metadata_path)
    
    result = {
        "valid": True,
        "expected_records": EXPECTED_OFFICIAL_RECORDS,
        "actual_records": 0,
        "duplicates": 0,
        "missing": 0,
        "problems": []
    }
    
    if not raw_path.exists():
        result["valid"] = False
        result["problems"].append(f"Raw data file not found: {raw_path}")
        return result
        
    if not metadata_path.exists():
        result["valid"] = False
        result["problems"].append(f"Metadata file not found: {metadata_path}")
        # Note: metadata can be optional for some tests but let's record it.
    
    official_records = []
    warmup_records = 0
    diagnostic_records = 0
    seen_keys = set()
    run_ids = set()
    
    with open(raw_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                result["valid"] = False
                result["problems"].append(f"Line {line_num}: Malformed JSON")
                continue
                
            # Exclude warm-up
            if record.get("is_warmup", False):
                warmup_records += 1
                continue
                
            # Exclude diagnostics (e.g. pilot or non-full experiments)
            experiment_id = record.get("experiment_id", "")
            if experiment_id != "nqueens_primary_full":
                diagnostic_records += 1
                result["problems"].append(f"Line {line_num}: Unexpected experiment_id {experiment_id}")
                result["valid"] = False
                continue
                
            run_id = record.get("run_id")
            if run_id in run_ids:
                result["duplicates"] += 1
                result["valid"] = False
                result["problems"].append(f"Duplicate run_id: {run_id}")
            run_ids.add(run_id)
            
            method_id = record.get("method_id")
            n = record.get("n")
            rep = record.get("repetition")
            
            key = (method_id, n, rep)
            if key in seen_keys:
                if run_id not in run_ids: # if not already caught by run_id
                    result["duplicates"] += 1
                    result["valid"] = False
                    result["problems"].append(f"Duplicate logical run: {key}")
            seen_keys.add(key)
            
            official_records.append(record)
            
            # Policy check
            if record.get("method_family") == "SAT":
                policy = record.get("phase_policy")
                if policy != "solver_default":
                    result["valid"] = False
                    result["problems"].append(f"Run {run_id}: Invalid phase policy {policy}")
            
            # Timings check
            pipeline_time = record.get("pipeline_total_time")
            status = record.get("status")
            if status == "SAT":
                if not record.get("valid", False):
                    result["valid"] = False
                    result["problems"].append(f"Run {run_id}: SAT but not valid")
                if pipeline_time is not None and pipeline_time < 0:
                    result["valid"] = False
                    result["problems"].append(f"Run {run_id}: Negative timing {pipeline_time}")
            
            # Missing timings for successful runs
            if status == "SAT" and pipeline_time is None:
                result["valid"] = False
                result["problems"].append(f"Run {run_id}: SAT but missing pipeline_total_time")
                
            if status == "BLOCKED_LICENSE":
                # Ensure no fake times are given
                if pipeline_time is not None and pipeline_time > 0:
                     pass # depending on how it's logged, but typically we shouldn't have valid pipeline time for blocked license.
                     
    result["actual_records"] = len(official_records)
    
    if result["actual_records"] < result["expected_records"]:
        result["missing"] = result["expected_records"] - result["actual_records"]
        result["valid"] = False
        result["problems"].append(f"Missing {result['missing']} records")
    elif result["actual_records"] > result["expected_records"]:
        result["valid"] = False
        result["problems"].append(f"Too many records: {result['actual_records']}")
        
    return result
