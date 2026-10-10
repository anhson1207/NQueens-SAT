import tempfile
import unittest
from pathlib import Path

import pandas as pd

from experiments.solver_registry import METHODS
from experiments.visualization.export_tables import _export_table2_exact_summary
from experiments.visualization.plot_config import (
    EXACT_METHODS,
    METHOD_COLORS,
    METHOD_LABELS,
    METHOD_MARKERS,
    SAT_METHODS,
)


class TestVisualizationMethodIdentifiers(unittest.TestCase):
    def test_visualization_registry_matches_solver_registry(self):
        canonical = set(METHODS)
        self.assertEqual(set(METHOD_LABELS), canonical)
        self.assertEqual(set(METHOD_COLORS), canonical)
        self.assertEqual(set(METHOD_MARKERS), canonical)
        self.assertEqual(set(SAT_METHODS) | set(EXACT_METHODS), canonical)
        self.assertIn("cp_sat", EXACT_METHODS)
        self.assertNotIn("or_tools_cp_sat", canonical)

    def test_exact_summary_exports_cp_sat(self):
        dataframe = pd.DataFrame(
            [
                {
                    "method_id": "cp_sat",
                    "n": 100,
                    "status": "SAT",
                    "valid": True,
                    "pipeline_total_time": 0.5,
                }
            ]
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            _export_table2_exact_summary(dataframe, output)
            table = pd.read_csv(output / "table02_exact_solver_summary.csv")
        self.assertEqual(table["Method"].tolist(), ["OR-Tools CP-SAT"])


if __name__ == "__main__":
    unittest.main()
