import unittest
import os
from experiments.benchmark_runner import export_raw_csv

class TestBenchmarkOutput(unittest.TestCase):
    def test_export_raw_csv(self):
        records = [
            {"experiment_id": "e1", "run_id": "r1", "method_id": "m1", "n": 4, "repetition": 1, "status": "SAT", "valid": True},
            {"experiment_id": "e1", "run_id": "r2", "method_id": "m2", "n": 4, "repetition": 1, "status": "TIMEOUT", "valid": None}
        ]
        
        path = "test_export.csv"
        try:
            export_raw_csv(records, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 3) # header + 2 rows
                self.assertTrue("experiment_id" in lines[0])
                self.assertTrue("SAT" in lines[1])
                self.assertTrue("TIMEOUT" in lines[2])
        finally:
            if os.path.exists(path):
                os.remove(path)

