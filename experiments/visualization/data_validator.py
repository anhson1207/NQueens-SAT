"""Strict integrity validation for the official Full benchmark dataset."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Dict

from experiments.benchmark_runner import (
    CPLEX_MIP_MAX_N,
    GUROBI_MAX_N,
    compute_config_fingerprint,
)
from experiments.solver_registry import METHODS, REGISTRY


FULL_EXPERIMENT_ID = "nqueens_primary_full"
FULL_N_VALUES = (4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100)
EXPECTED_REPETITIONS = 5
EXPECTED_METHODS = len(METHODS)
EXPECTED_N_VALUES = len(FULL_N_VALUES)
EXPECTED_OFFICIAL_RECORDS = EXPECTED_METHODS * EXPECTED_N_VALUES * EXPECTED_REPETITIONS
ALLOWED_STATUSES = {
    "SAT",
    "UNSAT",
    "TIMEOUT",
    "BLOCKED_LICENSE",
    "LICENSE_ERROR",
    "MISSING_CP_ENGINE",
    "ENVIRONMENT_ERROR",
    "VALIDATION_ERROR",
    "ERROR",
    "UNKNOWN",
}


def full_benchmark_config() -> Dict[str, Any]:
    """Return the canonical configuration used by the primary Full benchmark."""
    return {
        "experiment_id": FULL_EXPERIMENT_ID,
        "mode": "full",
        "n_values": list(FULL_N_VALUES),
        "repeats": EXPECTED_REPETITIONS,
        "methods": list(METHODS),
        "timeout": 300,
        "external_timeout": 330,
        "sat_phase_policy": "solver_default",
        "workers": 1,
        "random_seed": 0,
        "schedule_seed": 2026,
    }


def expected_official_keys() -> set[tuple[str, int, int]]:
    return {
        (method, n, repetition)
        for repetition in range(1, EXPECTED_REPETITIONS + 1)
        for n in FULL_N_VALUES
        for method in METHODS
    }


def _canonical_run_id(method: str, n: int, repetition: int) -> str:
    return f"{FULL_EXPERIMENT_ID}_{method}_n{n}_r{repetition}"


def _blocked_by_declared_license(method: str, n: int) -> bool:
    return (
        (method == "gurobi_mip" and n > GUROBI_MAX_N)
        or (method == "cplex_mip" and n > CPLEX_MIP_MAX_N)
    )


def validate_full_benchmark_dataset(
    raw_path: str | Path,
    metadata_path: str | Path,
) -> Dict[str, Any]:
    """Validate exact coverage, identity, configuration, results, and timings."""
    raw_path = Path(raw_path)
    metadata_path = Path(metadata_path)
    expected_keys = expected_official_keys()
    expected_config = full_benchmark_config()
    expected_fingerprint = compute_config_fingerprint(expected_config)

    result: Dict[str, Any] = {
        "valid": True,
        "expected_records": EXPECTED_OFFICIAL_RECORDS,
        "actual_records": 0,
        "unique_trial_keys": 0,
        "unique_run_ids": 0,
        "duplicates": 0,
        "duplicate_run_ids": 0,
        "duplicate_trial_keys": 0,
        "missing": EXPECTED_OFFICIAL_RECORDS,
        "missing_keys": [],
        "unexpected_keys": [],
        "warmup_records": 0,
        "warmup_duplicate_run_ids": 0,
        "diagnostic_records": 0,
        "malformed_records": 0,
        "legacy_records_without_fingerprint": 0,
        "status_counts": {},
        "config_fingerprint": expected_fingerprint,
        "problems": [],
    }

    def problem(message: str) -> None:
        result["valid"] = False
        result["problems"].append(message)

    if not raw_path.exists():
        problem(f"Raw data file not found: {raw_path}")
        return result

    metadata: Dict[str, Any] = {}
    if not metadata_path.exists():
        problem(f"Metadata file not found: {metadata_path}")
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            problem(f"Metadata is unreadable or malformed: {exc}")
        else:
            if metadata.get("experiment_id") != FULL_EXPERIMENT_ID:
                problem(
                    "Metadata experiment_id mismatch: "
                    f"{metadata.get('experiment_id')!r}"
                )
            if metadata.get("config_fingerprint") != expected_fingerprint:
                problem(
                    "Metadata config_fingerprint mismatch or missing: "
                    f"{metadata.get('config_fingerprint')!r}"
                )

    run_ids: set[str] = set()
    trial_keys: set[tuple[str, int, int]] = set()
    duplicate_run_ids: set[str] = set()
    duplicate_keys: set[tuple[str, int, int]] = set()
    unexpected_keys: set[tuple[Any, Any, Any]] = set()
    warmup_run_ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    official_records = 0

    with raw_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                result["malformed_records"] += 1
                problem(f"Line {line_number}: malformed JSON")
                continue
            if not isinstance(record, dict):
                problem(f"Line {line_number}: record is not a JSON object")
                continue

            if record.get("is_warmup", False):
                result["warmup_records"] += 1
                warmup_id = record.get("run_id")
                if warmup_id in warmup_run_ids:
                    result["warmup_duplicate_run_ids"] += 1
                warmup_run_ids.add(warmup_id)
                if (
                    record.get("experiment_id") != FULL_EXPERIMENT_ID
                    or record.get("method_id") not in METHODS
                    or record.get("n") != 4
                    or record.get("repetition") != 0
                ):
                    problem(f"Line {line_number}: invalid warm-up record")
                continue

            if record.get("experiment_id") != FULL_EXPERIMENT_ID:
                result["diagnostic_records"] += 1
                problem(
                    f"Line {line_number}: unexpected experiment_id "
                    f"{record.get('experiment_id')!r}"
                )
                continue

            official_records += 1
            method = record.get("method_id")
            n = record.get("n")
            repetition = record.get("repetition")
            key = (method, n, repetition)
            run_id = record.get("run_id")

            if run_id in run_ids:
                duplicate_run_ids.add(run_id)
                problem(f"Line {line_number}: duplicate official run_id {run_id!r}")
            run_ids.add(run_id)
            if key in trial_keys:
                duplicate_keys.add(key)
                problem(f"Line {line_number}: duplicate official trial key {key!r}")
            trial_keys.add(key)

            if key not in expected_keys:
                unexpected_keys.add(key)
                problem(f"Line {line_number}: unexpected official trial key {key!r}")
            elif run_id != _canonical_run_id(method, n, repetition):
                problem(
                    f"Line {line_number}: non-canonical run_id {run_id!r} for {key!r}"
                )

            for field, expected in (
                ("workers", 1),
                ("random_seed", 0),
                ("internal_timeout", 300),
                ("external_timeout", 330),
            ):
                if record.get(field) != expected:
                    problem(
                        f"Line {line_number}: {field}={record.get(field)!r}, "
                        f"expected {expected!r}"
                    )

            if method in REGISTRY and REGISTRY[method]["method_family"] == "SAT":
                if record.get("phase_policy") != "solver_default":
                    problem(
                        f"Line {line_number}: invalid SAT phase policy "
                        f"{record.get('phase_policy')!r}"
                    )
            elif record.get("phase_policy") is not None:
                problem(f"Line {line_number}: non-SAT record has phase_policy")

            fingerprint = record.get("config_fingerprint")
            if fingerprint is None:
                result["legacy_records_without_fingerprint"] += 1
            elif fingerprint != expected_fingerprint:
                problem(
                    f"Line {line_number}: config_fingerprint mismatch {fingerprint!r}"
                )

            status = record.get("status")
            status_counts[str(status)] += 1
            if status not in ALLOWED_STATUSES:
                problem(f"Line {line_number}: unsupported status {status!r}")
            pipeline_time = record.get("pipeline_total_time")
            process_time = record.get("process_wall_time")
            if pipeline_time is not None and (
                not isinstance(pipeline_time, (int, float)) or pipeline_time < 0
            ):
                problem(f"Line {line_number}: invalid pipeline_total_time")
            if process_time is not None and (
                not isinstance(process_time, (int, float)) or process_time < 0
            ):
                problem(f"Line {line_number}: invalid process_wall_time")

            if status == "SAT":
                if record.get("valid") is not True:
                    problem(f"Line {line_number}: SAT record is not valid=True")
                if pipeline_time is None:
                    problem(f"Line {line_number}: SAT record lacks pipeline_total_time")
                if record.get("executed") is not True:
                    problem(f"Line {line_number}: SAT record must have executed=True")
                if record.get("queen_count") != n:
                    problem(f"Line {line_number}: SAT queen_count does not equal N")

            expected_block = (
                isinstance(n, int)
                and isinstance(method, str)
                and _blocked_by_declared_license(method, n)
            )
            if status == "BLOCKED_LICENSE":
                if not expected_block:
                    problem(f"Line {line_number}: unexpected BLOCKED_LICENSE")
                if record.get("executed") is not False:
                    problem(
                        f"Line {line_number}: BLOCKED_LICENSE must have executed=False"
                    )
                if pipeline_time is not None or process_time is not None:
                    problem(f"Line {line_number}: blocked license has runtime")
            elif expected_block:
                problem(f"Line {line_number}: expected proactive BLOCKED_LICENSE")

    missing_keys = expected_keys - trial_keys
    result["actual_records"] = official_records
    result["unique_trial_keys"] = len(trial_keys)
    result["unique_run_ids"] = len(run_ids)
    
    # Accurate count of extra records that are duplicates of already seen ones
    result["duplicate_run_ids"] = official_records - len(run_ids)
    result["duplicate_trial_keys"] = official_records - len(trial_keys)
    result["duplicates"] = official_records - len(trial_keys)
    result["missing"] = len(missing_keys)
    result["missing_keys"] = [list(key) for key in sorted(missing_keys)]
    result["unexpected_keys"] = [
        list(key) for key in sorted(unexpected_keys, key=repr)
    ]
    result["status_counts"] = dict(sorted(status_counts.items()))

    if missing_keys:
        problem(f"Missing {len(missing_keys)} expected trial keys")
    if official_records != EXPECTED_OFFICIAL_RECORDS:
        problem(
            f"Official record count is {official_records}, "
            f"expected {EXPECTED_OFFICIAL_RECORDS}"
        )
    if metadata:
        declared_legacy = metadata.get("legacy_records_without_fingerprint")
        if declared_legacy != result["legacy_records_without_fingerprint"]:
            problem(
                "Metadata legacy_records_without_fingerprint mismatch: "
                f"{declared_legacy!r} vs "
                f"{result['legacy_records_without_fingerprint']}"
            )
    if sum(status_counts.values()) != official_records:
        problem("Status counts do not sum to the official record count")

    return result
