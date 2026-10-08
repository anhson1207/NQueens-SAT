import unittest
import pandas as pd
from pathlib import Path
import tempfile
from experiments.visualization.export_tables import _export_table3_n20, _export_table1_sat_n100

class TestVisualizationAggregation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a mock dataframe
        self.df = pd.DataFrame([
            {"method_id": "sat_pairwise", "n": 20, "status": "SAT", "valid": True, "pipeline_total_time": 10.0, "method_family": "SAT"},
            {"method_id": "sat_pairwise", "n": 20, "status": "SAT", "valid": True, "pipeline_total_time": 20.0, "method_family": "SAT"},
            {"method_id": "sat_pairwise", "n": 20, "status": "TIMEOUT", "valid": False, "pipeline_total_time": None, "method_family": "SAT"},
            
            {"method_id": "sat_pairwise", "n": 100, "status": "SAT", "valid": True, "pipeline_total_time": 50.0, "primary_variables": 10000, "auxiliary_variables": 500, "clauses": 20000},
            {"method_id": "sat_pairwise", "n": 100, "status": "TIMEOUT", "valid": False, "pipeline_total_time": None, "primary_variables": 10000, "auxiliary_variables": 500, "clauses": 20000},
        ])
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_aggregation_n20(self):
        _export_table3_n20(self.df, self.output_dir)
        csv_path = self.output_dir / "table03_all_methods_n20.csv"
        self.assertTrue(csv_path.exists())
        
        df_out = pd.read_csv(csv_path)
        # We only have one method at N=20
        self.assertEqual(len(df_out), 1)
        row = df_out.iloc[0]
        
        self.assertEqual(row["Successful Runs"], 2) # TIMEOUT is ignored for successful count
        self.assertEqual(row["Median Runtime"], 15.0) # Median of 10 and 20
        
    def test_aggregation_n100(self):
        _export_table1_sat_n100(self.df, self.output_dir)
        csv_path = self.output_dir / "table01_sat_n100.csv"
        self.assertTrue(csv_path.exists())
        
        df_out = pd.read_csv(csv_path)
        self.assertEqual(len(df_out), 1)
        row = df_out.iloc[0]
        
        self.assertEqual(row["Successful Runs"], 1)
        self.assertEqual(row["Timeout Runs"], 1)
        self.assertEqual(row["Median Runtime"], 50.0)

if __name__ == "__main__":
    unittest.main()
