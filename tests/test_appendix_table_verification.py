import json
import unittest
from pathlib import Path

from scripts.generate_appendix_table import (
    a_sequential,
    build_table_rows,
    c_pairwise,
    c_sequential,
)
from src.sat.encodings.pairwise import encode_nqueens_pairwise
from src.sat.encodings.sequential import encode_nqueens_sequential

ROOT = Path(__file__).resolve().parent.parent


class TestAppendixTableVerification(unittest.TestCase):
    def setUp(self):
        self.benchmark_ns = [4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100]

    def test_pairwise_formula_matches_actual_cnf_generator(self):
        for n in self.benchmark_ns:
            expected_clauses = c_pairwise(n)
            actual_clauses = len(encode_nqueens_pairwise(n))
            self.assertEqual(
                actual_clauses,
                expected_clauses,
                f"Pairwise clause mismatch at N={n}: generated={actual_clauses}, formula={expected_clauses}",
            )

    def test_sequential_formula_matches_actual_cnf_generator(self):
        for n in self.benchmark_ns + [200]:
            expected_clauses = c_sequential(n)
            expected_aux = a_sequential(n)
            clauses, total_vars = encode_nqueens_sequential(n)
            actual_clauses = len(clauses)
            actual_aux = total_vars - n * n
            self.assertEqual(
                actual_clauses,
                expected_clauses,
                f"Sequential clause mismatch at N={n}: generated={actual_clauses}, formula={expected_clauses}",
            )
            self.assertEqual(
                actual_aux,
                expected_aux,
                f"Sequential aux variable mismatch at N={n}: generated={actual_aux}, formula={expected_aux}",
            )

    def test_formulas_match_raw_benchmark_records(self):
        raw_log_path = ROOT / "results" / "raw" / "benchmark_nqueens_primary_full.jsonl"
        self.assertTrue(raw_log_path.exists(), "Raw benchmark log must exist")

        checked_counts = {"sat_pairwise": 0, "sat_sequential": 0}
        with open(raw_log_path, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                method = r.get("method_id")
                n = r.get("n")
                clauses = r.get("clauses")
                if method == "sat_pairwise" and n in self.benchmark_ns:
                    self.assertEqual(
                        clauses,
                        c_pairwise(n),
                        f"Raw log Pairwise mismatch at N={n}",
                    )
                    checked_counts["sat_pairwise"] += 1
                elif method == "sat_sequential" and n in self.benchmark_ns:
                    self.assertEqual(
                        clauses,
                        c_sequential(n),
                        f"Raw log Sequential clause mismatch at N={n}",
                    )
                    self.assertEqual(
                        r.get("auxiliary_variables"),
                        a_sequential(n),
                        f"Raw log Sequential aux mismatch at N={n}",
                    )
                    checked_counts["sat_sequential"] += 1

        self.assertGreater(checked_counts["sat_pairwise"], 0)
        self.assertGreater(checked_counts["sat_sequential"], 0)

    def test_table_rows_distinguishes_n200_blocked_pairwise(self):
        rows = build_table_rows(self.benchmark_ns + [200])
        row_n200 = next(r for r in rows if r["n"] == 200)
        self.assertEqual(row_n200["pw_formula"], "13,253,800")
        self.assertEqual(row_n200["pw_generated"], "---")
        self.assertEqual(row_n200["seq_formula"], "475,612")
        self.assertEqual(row_n200["seq_generated"], "475,612")


if __name__ == "__main__":
    unittest.main()
