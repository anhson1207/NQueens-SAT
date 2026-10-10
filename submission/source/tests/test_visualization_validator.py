import json
import tempfile
import unittest
from pathlib import Path

from experiments.solver_registry import METHODS, REGISTRY
from experiments.visualization.data_validator import (
    EXPECTED_OFFICIAL_RECORDS,
    FULL_EXPERIMENT_ID,
    FULL_N_VALUES,
    full_benchmark_config,
    validate_full_benchmark_dataset,
)
from experiments.benchmark_runner import compute_config_fingerprint


class TestVisualizationValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.raw_path = Path(self.temp_dir.name) / "test_benchmark.jsonl"
        self.metadata_path = Path(self.temp_dir.name) / "metadata.json"
        self.fingerprint = compute_config_fingerprint(full_benchmark_config())
        self.metadata_path.write_text(
            json.dumps(
                {
                    "experiment_id": FULL_EXPERIMENT_ID,
                    "config_fingerprint": self.fingerprint,
                    "legacy_records_without_fingerprint": 0,
                }
            ),
            encoding="utf-8",
        )

    def make_record(self, method, n, repetition):
        family = REGISTRY[method]["method_family"]
        blocked = (
            (method == "gurobi_mip" and n > 44)
            or (method == "cplex_mip" and n > 31)
        )
        return {
            "experiment_id": FULL_EXPERIMENT_ID,
            "run_id": f"{FULL_EXPERIMENT_ID}_{method}_n{n}_r{repetition}",
            "method_id": method,
            "method_family": family,
            "n": n,
            "repetition": repetition,
            "is_warmup": False,
            "status": "BLOCKED_LICENSE" if blocked else "SAT",
            "executed": not blocked,
            "valid": None if blocked else True,
            "queen_count": None if blocked else n,
            "phase_policy": "solver_default" if family == "SAT" else None,
            "workers": 1,
            "random_seed": 0,
            "internal_timeout": 300,
            "external_timeout": 330,
            "pipeline_total_time": None if blocked else 0.1,
            "process_wall_time": None if blocked else 0.2,
            "config_fingerprint": self.fingerprint,
        }

    def valid_records(self):
        return [
            self.make_record(method, n, repetition)
            for repetition in range(1, 6)
            for n in FULL_N_VALUES
            for method in METHODS
        ]

    def write_records(self, records, malformed_line=None):
        with self.raw_path.open("w", encoding="utf-8") as output:
            for record in records:
                output.write(json.dumps(record) + "\n")
            if malformed_line is not None:
                output.write(malformed_line + "\n")

    def validate(self):
        return validate_full_benchmark_dataset(self.raw_path, self.metadata_path)

    def test_complete_cartesian_dataset_passes(self):
        self.write_records(self.valid_records())
        result = self.validate()
        self.assertTrue(result["valid"], result["problems"])
        self.assertEqual(result["actual_records"], EXPECTED_OFFICIAL_RECORDS)
        self.assertEqual(result["missing"], 0)

    def test_495_records_with_one_missing_and_one_duplicate_fails(self):
        records = self.valid_records()
        records[-1] = dict(records[0], run_id="different_id_same_logical_trial")
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["actual_records"], EXPECTED_OFFICIAL_RECORDS)
        self.assertEqual(result["missing"], 1)
        self.assertEqual(result["duplicate_trial_keys"], 1)

    def test_different_run_ids_for_same_trial_are_detected(self):
        records = self.valid_records()
        records.append(dict(records[0], run_id="second_run_id"))
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicate_trial_keys"], 1)

    def test_warmup_disguised_as_official_is_rejected(self):
        records = self.valid_records()
        records[0] = self.make_record("sat_pairwise", 4, 0)
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(result["unexpected_keys"])

    def test_invalid_sat_phase_policy_is_rejected(self):
        records = self.valid_records()
        records[0]["phase_policy"] = "legacy"
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(any("phase policy" in p for p in result["problems"]))

    def test_malformed_record_is_rejected(self):
        self.write_records(self.valid_records(), malformed_line='{ "broken":')
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["malformed_records"], 1)

    def test_wrong_experiment_id_is_rejected(self):
        records = self.valid_records()
        records[0]["experiment_id"] = "wrong_experiment"
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["diagnostic_records"], 1)

    def test_duplicate_run_id_is_rejected(self):
        records = self.valid_records()
        records[1]["run_id"] = records[0]["run_id"]
        self.write_records(records)
        result = self.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicate_run_ids"], 1)


if __name__ == "__main__":
    unittest.main()
