import unittest
import pandas as pd
import tempfile
import matplotlib
# Use Agg backend for testing to prevent window popups
matplotlib.use('Agg')

from pathlib import Path
from experiments.visualization.plot_sat_runtime import plot_sat_runtime_vs_n

class TestVisualizationExports(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        self.df = pd.DataFrame([
            {"method_id": "sat_pairwise", "n": 4, "status": "SAT", "valid": True, "pipeline_total_time": 0.01},
            {"method_id": "sat_pairwise", "n": 8, "status": "SAT", "valid": True, "pipeline_total_time": 0.05},
        ])
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_plot_sat_runtime_export(self):
        plot_sat_runtime_vs_n(self.df, self.output_dir)
        
        png_path = self.output_dir / "fig01_sat_runtime_vs_n.png"
        pdf_path = self.output_dir / "fig01_sat_runtime_vs_n.pdf"
        
        self.assertTrue(png_path.exists())
        self.assertTrue(pdf_path.exists())
        
        self.assertGreater(png_path.stat().st_size, 0)
        self.assertGreater(pdf_path.stat().st_size, 0)

if __name__ == "__main__":
    unittest.main()
