import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from experiments.benchmark_runner import (
    build_cli_command,
    compute_config_fingerprint,
    execute_trial,
    generate_schedule,
    load_and_validate_resume_state,
    parse_stdout_json,
)


def recovery_test_config():
    return {
        "experiment_id": "recovery_test",
        "mode": "full",
        "n_values": [4],
        "repeats": 1,
        "methods": ["sat_pairwise", "cp_sat"],
        "timeout": 300,
        "external_timeout": 330,
        "sat_phase_policy": "solver_default",
        "workers": 1,
        "random_seed": 0,
        "schedule_seed": 2026,
    }


def recovery_record(config, trial, schedule_index):
    run_id = (
        f"{config['experiment_id']}_{trial['method_id']}_"
        f"n{trial['n']}_r{trial['repetition']}"
    )
    is_sat = trial["method_id"].startswith("sat_")
    return {
        "experiment_id": config["experiment_id"],
        "run_id": run_id,
        "method_id": trial["method_id"],
        "method_family": "SAT" if is_sat else "CP-SAT",
        "n": trial["n"],
        "repetition": trial["repetition"],
        "executed": True,
        "status": "SAT",
        "valid": True,
        "phase_policy": config["sat_phase_policy"] if is_sat else None,
        "workers": config["workers"],
        "random_seed": config["random_seed"],
        "internal_timeout": config["timeout"],
        "external_timeout": config["external_timeout"],
        "pipeline_total_time": 0.1,
        "command": build_cli_command(trial["method_id"], trial["n"], config),
        "is_warmup": trial["is_warmup"],
        "schedule_index": schedule_index,
    }

class TestBenchmarkRunner(unittest.TestCase):
    def test_parse_stdout_json(self):
        # Normal
        s1 = '{"status": "SAT", "valid": true}'
        self.assertEqual(parse_stdout_json(s1), {"status": "SAT", "valid": True})
        
        # With trailing newline and prefix
        s2 = 'Warning something\n{"status": "UNSAT"}\n'
        self.assertEqual(parse_stdout_json(s2), {"status": "UNSAT"})
        
        # Invalid
        self.assertIsNone(parse_stdout_json('no json here'))
        
    @patch("experiments.benchmark_runner.subprocess.run")
    def test_execute_trial_success(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.stdout = '{"status": "SAT", "native_status": "SAT", "has_solution": true, "valid": true, "positions": [1,2,3,4], "total_time": 0.5}'
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        
        trial = {"method_id": "sat_binary", "n": 4, "repetition": 1}
        config = {"experiment_id": "test", "timeout": 300, "external_timeout": 330, "workers": 1, "random_seed": 0}
        
        record = execute_trial(trial, config, "test_run_1")
        self.assertTrue(record["executed"])
        self.assertEqual(record["status"], "SAT")
        self.assertTrue(record["valid"])
        self.assertEqual(record["queen_count"], 4)
        self.assertEqual(record["pipeline_total_time"], 0.5)
        
    def test_execute_trial_blocked_license(self):
        trial = {"method_id": "gurobi_mip", "n": 50, "repetition": 1}
        config = {"experiment_id": "test", "timeout": 300, "external_timeout": 330, "workers": 1, "random_seed": 0}
        
        record = execute_trial(trial, config, "test_run_2")
        self.assertFalse(record["executed"])
        self.assertEqual(record["status"], "BLOCKED_LICENSE")
        
    @patch("experiments.benchmark_runner.subprocess.run")
    def test_execute_trial_validation_error(self, mock_run):
        mock_proc = MagicMock()
        # Solver says SAT but valid is false
        mock_proc.stdout = '{"status": "SAT", "valid": false, "positions": [1,2,3,4]}'
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        
        trial = {"method_id": "cp_sat", "n": 4, "repetition": 1}
        config = {"experiment_id": "test", "timeout": 300, "external_timeout": 330, "workers": 1, "random_seed": 0}
        
        record = execute_trial(trial, config, "test_run_3")
        self.assertEqual(record["status"], "VALIDATION_ERROR")
        
    @patch("experiments.benchmark_runner.subprocess.run")
    def test_execute_trial_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=330)
        
        trial = {"method_id": "sat_product", "n": 100, "repetition": 1}
        config = {"experiment_id": "test", "timeout": 300, "external_timeout": 330, "workers": 1, "random_seed": 0}
        
        record = execute_trial(trial, config, "test_run_4")
        self.assertEqual(record["status"], "TIMEOUT")
        self.assertEqual(record["error_category"], "EXTERNAL_TIMEOUT")


class TestResumeIntegrity(unittest.TestCase):
    def setUp(self):
        self.config = recovery_test_config()
        self.schedule = generate_schedule(
            self.config["n_values"],
            self.config["methods"],
            self.config["repeats"],
            self.config["schedule_seed"],
        )

    def write_records(self, records, malformed_line=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "raw.jsonl"
        with path.open("w", encoding="utf-8") as output:
            for record in records:
                output.write(json.dumps(record) + "\n")
            if malformed_line is not None:
                output.write(malformed_line + "\n")
        return path

    def test_config_fingerprint_is_stable_and_sensitive(self):
        fingerprint = compute_config_fingerprint(self.config)
        reordered = dict(reversed(list(self.config.items())))
        self.assertEqual(fingerprint, compute_config_fingerprint(reordered))
        changed = dict(self.config, sat_phase_policy="legacy")
        self.assertNotEqual(fingerprint, compute_config_fingerprint(changed))

    def test_legacy_records_are_validated_without_retroactive_fingerprint(self):
        records = [
            recovery_record(self.config, trial, index)
            for index, trial in enumerate(self.schedule)
        ]
        # Preserve a historical duplicate warm-up: it is reported but never counted
        # as an official trial or rewritten.
        records.insert(1, dict(records[0]))
        state = load_and_validate_resume_state(
            self.write_records(records), self.schedule, self.config
        )
        self.assertEqual(len(state["official_records"]), 2)
        self.assertEqual(state["legacy_records_without_fingerprint"], 2)
        self.assertEqual(state["warmup_duplicate_records"], 1)
        self.assertEqual(state["missing_keys"], set())

    def test_malformed_json_aborts_resume(self):
        path = self.write_records([], malformed_line='{ "broken":')
        with self.assertRaisesRegex(ValueError, "Malformed JSON"):
            load_and_validate_resume_state(path, self.schedule, self.config)

    def test_configuration_mismatch_aborts_resume(self):
        record = recovery_record(self.config, self.schedule[-1], len(self.schedule) - 1)
        record["phase_policy"] = "legacy"
        with self.assertRaisesRegex(ValueError, "phase_policy"):
            load_and_validate_resume_state(
                self.write_records([record]), self.schedule, self.config
            )

    def test_duplicate_official_key_aborts_resume(self):
        trial = self.schedule[-1]
        record = recovery_record(self.config, trial, len(self.schedule) - 1)
        duplicate = dict(record)
        with self.assertRaisesRegex(ValueError, "duplicate official"):
            load_and_validate_resume_state(
                self.write_records([record, duplicate]), self.schedule, self.config
            )
