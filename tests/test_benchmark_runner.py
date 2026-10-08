import unittest
from unittest.mock import patch, MagicMock
from experiments.benchmark_runner import execute_trial, parse_stdout_json

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

