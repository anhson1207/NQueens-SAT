"""Exercise the complete Pairwise-to-Glucose3 pipeline and its CLI on small N."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from src.common.validator import validate_positions
from src.sat.solver import solve_nqueens_pairwise


class TestPairwiseIntegration(unittest.TestCase):
    def _check_result(self, n: int, expected_status: str) -> dict:
        result = solve_nqueens_pairwise(n)
        self.assertEqual(result["method"], "SAT")
        self.assertEqual(result["solver"], "Glucose3")
        self.assertEqual(result["encoding"], "pairwise")
        self.assertEqual(result["n"], n)
        self.assertEqual(result["status"], expected_status, result["error"])
        self.assertEqual(result["primary_variables"], n * n)
        self.assertEqual(result["auxiliary_variables"], 0)
        self.assertEqual(result["total_variables"], n * n)
        self.assertGreater(result["clauses"], 0)
        self.assertIsNone(result["error"])
        self.assertEqual(result["solve_time"], result["load_time"] + result["search_time"])
        self.assertGreaterEqual(
            result["total_time"],
            result["encoding_time"] + result["solve_time"] + result["decode_validate_time"],
        )
        if expected_status == "SAT":
            self.assertIs(result["has_solution"], True)
            self.assertIs(result["valid"], True)
            self.assertEqual(len(result["positions"]), n)
            self.assertTrue(validate_positions(result["positions"], n))
        else:
            self.assertIs(result["has_solution"], False)
            self.assertIsNone(result["positions"])
            self.assertIsNone(result["valid"])
        return result

    def test_n1(self) -> None:
        self.assertEqual(self._check_result(1, "SAT")["positions"], [(0, 0)])

    def test_n2(self) -> None:
        self._check_result(2, "UNSAT")

    def test_n3(self) -> None:
        self._check_result(3, "UNSAT")

    def test_n4(self) -> None:
        result = self._check_result(4, "SAT")
        self.assertEqual(result["clauses"], 84)

    def test_n5(self) -> None:
        self._check_result(5, "SAT")

    def test_n8(self) -> None:
        self._check_result(8, "SAT")

    def test_invalid_board_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve_nqueens_pairwise(n)


class TestPairwiseCLI(unittest.TestCase):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "src.sat.solver", *args],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def test_json_sat_is_one_object_even_with_print_board(self) -> None:
        process = self._run_cli("--n", "4", "--json", "--print-board")
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(len(process.stdout.splitlines()), 1)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(validate_positions(result["positions"], 4))
        self.assertNotIn("cnf", result)
        self.assertNotIn("board", result)

    def test_json_unsat_is_successful_execution(self) -> None:
        process = self._run_cli("--n", "2", "--json")
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIsNone(result["positions"])
        self.assertIsNone(result["valid"])

    def test_prints_valid_board_when_requested(self) -> None:
        process = self._run_cli("--n", "4", "--print-board")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Status: SAT", process.stdout)
        board = [line.split() for line in process.stdout.splitlines()[-4:]]
        self.assertTrue(all(len(row) == 4 for row in board))
        positions = [
            (row, col) for row in range(4) for col in range(4) if board[row][col] == "Q"
        ]
        self.assertTrue(validate_positions(positions, 4))

    def test_default_summary_has_no_board(self) -> None:
        process = self._run_cli("--n", "4")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Status: SAT", process.stdout)
        self.assertFalse(any("Q" in line.split() for line in process.stdout.splitlines()))

    def test_invalid_n_reports_error_and_nonzero_exit(self) -> None:
        process = self._run_cli("--n", "0", "--json")
        self.assertNotEqual(process.returncode, 0)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("ValueError", result["error"])


if __name__ == "__main__":
    unittest.main()
