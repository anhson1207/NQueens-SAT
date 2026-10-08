"""Solve Sequential N=20, 50, 100 in child processes with whole-run timeouts."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from src.common.validator import validate_positions


class TestLargeSequentialSolver(unittest.TestCase):
    timeout_seconds = 300
    expected_counts = {
        20: (400, 1_482, 1_882, 4_372),
        50: (2_500, 9_702, 12_202, 28_912),
        100: (10_000, 39_402, 49_402, 117_812),
    }

    def _check_solution(self, n: int) -> None:
        try:
            process = subprocess.run(
                [
                    sys.executable, "-m", "src.sat.solver",
                    "--encoding", "sequential", "--n", str(n), "--json",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, text=True, timeout=self.timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                f"Sequential N={n}: TIMEOUT after {self.timeout_seconds}s "
                "(entire child process)"
            )

        self.assertEqual(
            process.returncode, 0,
            f"Sequential N={n}: child exited {process.returncode}; "
            f"stderr={process.stderr}; stdout={process.stdout}",
        )
        result = json.loads(process.stdout)
        primary, auxiliary, total, clauses = self.expected_counts[n]
        self.assertEqual(result["n"], n)
        self.assertEqual(result["solver"], "Glucose3")
        self.assertEqual(result["encoding"], "sequential")
        self.assertEqual(result["status"], "SAT", result.get("error"))
        self.assertIs(result["has_solution"], True)
        self.assertIs(result["valid"], True)
        self.assertEqual(len(result["positions"]), n)
        self.assertTrue(validate_positions(result["positions"], n))
        self.assertEqual(result["primary_variables"], primary)
        self.assertEqual(result["auxiliary_variables"], auxiliary)
        self.assertEqual(result["total_variables"], total)
        self.assertEqual(result["clauses"], clauses)
        self.assertEqual(result["solve_time"], result["load_time"] + result["search_time"])
        for key in (
            "encoding_time", "load_time", "search_time", "solve_time",
            "decode_validate_time", "total_time",
        ):
            self.assertGreaterEqual(result[key], 0.0)
        self.assertGreaterEqual(
            result["total_time"],
            result["encoding_time"] + result["solve_time"] + result["decode_validate_time"],
        )
        self.assertIsInstance(result["statistics"], dict)
        summary = {key: value for key, value in result.items() if key != "positions"}
        print("\nLarge-instance result: " + json.dumps(summary), flush=True)

    def test_n020(self) -> None:
        self._check_solution(20)

    def test_n050(self) -> None:
        self._check_solution(50)

    def test_n100(self) -> None:
        self._check_solution(100)


if __name__ == "__main__":
    unittest.main()
