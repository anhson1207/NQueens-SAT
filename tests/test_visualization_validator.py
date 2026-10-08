import unittest
import json
import tempfile
from pathlib import Path
from experiments.visualization.data_validator import validate_full_benchmark_dataset, EXPECTED_OFFICIAL_RECORDS

class TestVisualizationValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_path = Path(self.temp_dir.name) / "test_benchmark.jsonl"
        self.metadata_path = Path(self.temp_dir.name) / "metadata.json"
        
        with open(self.metadata_path, "w") as f:
            json.dump({}, f)
            
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_missing_records(self):
        with open(self.raw_path, "w") as f:
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "run_id": "1", "method_id": "sat_pairwise", "n": 4, "repetition": 0, "status": "SAT", "valid": True}) + "\n")
            
        result = validate_full_benchmark_dataset(self.raw_path, self.metadata_path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["actual_records"], 1)
        self.assertEqual(result["missing"], EXPECTED_OFFICIAL_RECORDS - 1)
        
    def test_duplicate_run_id(self):
        with open(self.raw_path, "w") as f:
            for _ in range(2):
                f.write(json.dumps({"experiment_id": "nqueens_primary_full", "run_id": "duplicate_id", "method_id": "sat_pairwise", "n": 4, "repetition": 0, "status": "SAT", "valid": True}) + "\n")
                
        result = validate_full_benchmark_dataset(self.raw_path, self.metadata_path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Duplicate run_id" in p for p in result["problems"]))
        
    def test_invalid_sat_policy(self):
        with open(self.raw_path, "w") as f:
            f.write(json.dumps({
                "experiment_id": "nqueens_primary_full", "run_id": "1", "method_id": "sat_pairwise", "method_family": "SAT",
                "n": 4, "repetition": 0, "status": "SAT", "valid": True, "phase_policy": "custom_policy"
            }) + "\n")
            
        result = validate_full_benchmark_dataset(self.raw_path, self.metadata_path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid phase policy" in p for p in result["problems"]))
        
if __name__ == "__main__":
    unittest.main()
