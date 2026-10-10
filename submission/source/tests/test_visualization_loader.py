import unittest
import json
import pandas as pd
import tempfile
from pathlib import Path
from experiments.visualization.data_loader import load_full_benchmark_data

class TestVisualizationLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_path = Path(self.temp_dir.name) / "test_benchmark.jsonl"
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_load_valid_jsonl(self):
        with open(self.raw_path, "w") as f:
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "method_id": "sat_pairwise", "n": 4, "is_warmup": False}) + "\n")
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "method_id": "sat_binary", "n": 8, "is_warmup": False}) + "\n")
            
        df = load_full_benchmark_data(self.raw_path)
        self.assertEqual(len(df), 2)
        
    def test_exclude_warmup_and_invalid_experiments(self):
        with open(self.raw_path, "w") as f:
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "method_id": "sat_pairwise", "is_warmup": True}) + "\n")
            f.write(json.dumps({"experiment_id": "pilot", "method_id": "sat_pairwise", "is_warmup": False}) + "\n")
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "method_id": "sat_binary", "is_warmup": False}) + "\n")
            
        df = load_full_benchmark_data(self.raw_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["method_id"], "sat_binary")
        
    def test_malformed_json(self):
        with open(self.raw_path, "w") as f:
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "is_warmup": False}) + "\n")
            f.write("not json\n")
            f.write(json.dumps({"experiment_id": "nqueens_primary_full", "is_warmup": False}) + "\n")
            
        df = load_full_benchmark_data(self.raw_path)
        self.assertEqual(len(df), 2)
        
if __name__ == "__main__":
    unittest.main()
