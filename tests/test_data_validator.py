import json
import pytest
from pathlib import Path
from experiments.visualization.data_validator import (
    validate_full_benchmark_dataset,
    FULL_EXPERIMENT_ID,
    expected_official_keys,
)

@pytest.fixture
def base_records():
    # Generate exactly 495 valid records
    records = []
    for (method, n, rep) in expected_official_keys():
        records.append({
            "experiment_id": FULL_EXPERIMENT_ID,
            "run_id": f"{FULL_EXPERIMENT_ID}_{method}_n{n}_r{rep}",
            "method_id": method,
            "n": n,
            "repetition": rep,
            "is_warmup": False,
            "status": "SAT",
            "valid": True,
            "executed": True,
            "pipeline_total_time": 1.0,
            "process_wall_time": 1.5,
            "queen_count": n,
            "workers": 1,
            "random_seed": 0,
            "internal_timeout": 300,
            "external_timeout": 330,
            "phase_policy": "solver_default" if "sat" in method else None,
        })
    return records

def test_missing_and_duplicate(tmp_path, base_records):
    # Remove the last one, duplicate the first one
    records = base_records[:-1] + [base_records[0]]
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["valid"] is False
    assert res["actual_records"] == 495
    assert res["missing"] == 1
    assert res["duplicates"] == 1
    assert res["duplicate_trial_keys"] == 1

def test_different_run_id_same_key(tmp_path, base_records):
    records = base_records[:-1]
    duplicate = base_records[-1].copy()
    duplicate["run_id"] = "different_run_id"
    records.append(base_records[-1])
    records.append(duplicate)
    # now 496 records
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["valid"] is False
    assert res["actual_records"] == 496
    assert res["missing"] == 0
    assert res["duplicates"] == 1
    assert res["duplicate_run_ids"] == 0 # because all run_ids are unique!
    assert res["duplicate_trial_keys"] == 1 # because the key is duplicated

def test_warmup_mixed(tmp_path, base_records):
    records = base_records.copy()
    records.append({
        "experiment_id": FULL_EXPERIMENT_ID,
        "run_id": f"{FULL_EXPERIMENT_ID}_sat_pairwise_n4_r0",
        "method_id": "sat_pairwise",
        "n": 4,
        "repetition": 0,
        "is_warmup": True,
    })
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["warmup_records"] == 1
    assert res["actual_records"] == 495

def test_wrong_phase_policy(tmp_path, base_records):
    records = base_records.copy()
    # Find a SAT record
    for r in records:
        if "sat" in r["method_id"]:
            r["phase_policy"] = "aux_false"
            break
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["valid"] is False
    assert any("invalid SAT phase policy" in p for p in res["problems"])

def test_malformed_record(tmp_path, base_records):
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        f.write("{malformed json\n")
        for r in base_records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["valid"] is False
    assert res["malformed_records"] == 1

def test_wrong_experiment_id(tmp_path, base_records):
    records = base_records.copy()
    records[0]["experiment_id"] = "wrong_id"
    raw = tmp_path / "raw.jsonl"
    meta = tmp_path / "meta.json"
    with open(raw, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    meta.write_text("{}")
    
    res = validate_full_benchmark_dataset(raw, meta)
    assert res["valid"] is False
    assert res["diagnostic_records"] == 1
