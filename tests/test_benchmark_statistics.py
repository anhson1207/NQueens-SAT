import unittest
from experiments.benchmark_statistics import compute_statistics

class TestBenchmarkStatistics(unittest.TestCase):
    def test_compute_statistics(self):
        records = [
            {"method_id": "sat1", "n": 8, "executed": True, "status": "SAT", "valid": True, "pipeline_total_time": 1.0},
            {"method_id": "sat1", "n": 8, "executed": True, "status": "SAT", "valid": True, "pipeline_total_time": 2.0},
            {"method_id": "sat1", "n": 8, "executed": True, "status": "SAT", "valid": True, "pipeline_total_time": 3.0},
            {"method_id": "sat1", "n": 8, "executed": True, "status": "TIMEOUT", "valid": None, "pipeline_total_time": None},
        ]
        
        summaries = compute_statistics(records)
        self.assertEqual(len(summaries), 1)
        s = summaries[0]
        self.assertEqual(s["runs_planned"], 4)
        self.assertEqual(s["runs_executed"], 4)
        self.assertEqual(s["successful_runs"], 3)
        self.assertEqual(s["timeout_runs"], 1)
        self.assertEqual(s["success_rate"], 3 / 4)
        self.assertEqual(s["mean_time"], 2.0)
        self.assertEqual(s["median_time"], 2.0)
        self.assertEqual(s["min_time"], 1.0)
        self.assertEqual(s["max_time"], 3.0)
        self.assertAlmostEqual(s["std_time"], 1.0)
        
    def test_empty_successful(self):
        records = [
            {"method_id": "gurobi", "n": 50, "executed": False, "status": "BLOCKED_LICENSE", "valid": None, "pipeline_total_time": None},
        ]
        
        summaries = compute_statistics(records)
        s = summaries[0]
        self.assertEqual(s["runs_planned"], 1)
        self.assertEqual(s["runs_executed"], 0)
        self.assertEqual(s["successful_runs"], 0)
        self.assertEqual(s["license_blocked_runs"], 1)
        self.assertEqual(s["success_rate"], 0.0)
        self.assertIsNone(s["mean_time"])
        self.assertIsNone(s["std_time"])

