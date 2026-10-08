"""Check Commander solutions, four-encoding consistency and CLI selection."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from pysat.solvers import Glucose3

from src.common.validator import validate_positions
from src.sat.encodings.commander import encode_nqueens_commander
from src.sat.solver import (
    decode_sat_model,
    solve_nqueens_binary,
    solve_nqueens_commander,
    solve_nqueens_pairwise,
    solve_nqueens_sequential,
)


class TestCommanderIntegration(unittest.TestCase):
    def _check_result(self, n: int, expected: str) -> dict:
        result = solve_nqueens_commander(n)
        self.assertEqual(result["n"], n)
        self.assertEqual(result["encoding"], "commander")
        self.assertEqual(result["group_size"], 3)
        self.assertEqual(result["solver"], "Glucose3")
        self.assertEqual(result["status"], expected, result["error"])
        self.assertIsNone(result["error"])
        self.assertEqual(result["primary_variables"], n * n)
        self.assertEqual(result["total_variables"], n * n + result["auxiliary_variables"])
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
        if expected == "SAT":
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
        result = self._check_result(1, "SAT")
        self.assertEqual((result["auxiliary_variables"], result["clauses"]), (0, 2))

    def test_n2(self) -> None:
        self._check_result(2, "UNSAT")

    def test_n3(self) -> None:
        self._check_result(3, "UNSAT")

    def test_n4(self) -> None:
        result = self._check_result(4, "SAT")
        self.assertEqual(result["auxiliary_variables"], 20)
        self.assertEqual(result["total_variables"], 36)
        self.assertEqual(result["clauses"], 104)

    def test_n5(self) -> None:
        self._check_result(5, "SAT")

    def test_n8(self) -> None:
        self._check_result(8, "SAT")

    def test_invalid_arguments(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                solve_nqueens_commander(n)
        for group_size in (0, 1, True, 2.5):
            with self.subTest(group_size=group_size), self.assertRaises(ValueError):
                solve_nqueens_commander(4, group_size)

    def test_matches_other_encodings_status_and_validation(self) -> None:
        for n in (1, 2, 3, 4, 5, 8):
            with self.subTest(n=n):
                results = (
                    solve_nqueens_pairwise(n),
                    solve_nqueens_binary(n),
                    solve_nqueens_sequential(n),
                    solve_nqueens_commander(n),
                )
                expected = "UNSAT" if n in (2, 3) else "SAT"
                self.assertEqual({result["status"] for result in results}, {expected})
                for result in results:
                    if expected == "SAT":
                        self.assertIs(result["valid"], True)
                        self.assertTrue(validate_positions(result["positions"], n))
                    else:
                        self.assertIsNone(result["positions"])
                        self.assertIsNone(result["valid"])

    def test_real_positive_commanders_are_ignored_by_decoder(self) -> None:
        cnf, total = encode_nqueens_commander(4)
        with Glucose3(bootstrap_with=cnf) as solver:
            self.assertTrue(solver.solve())
            model = solver.get_model()
        self.assertTrue(any(16 < literal <= total for literal in model))
        positions = decode_sat_model(model, 4)
        self.assertEqual(len(positions), 4)
        self.assertTrue(validate_positions(positions, 4))


class TestCommanderCLI(unittest.TestCase):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "src.sat.solver", *args],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, timeout=30, check=False,
        )

    def test_commander_json_wins_over_print_board(self) -> None:
        process = self._run_cli(
            "--encoding", "commander", "--n", "4", "--json", "--print-board"
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(process.stdout.splitlines()), 1)
        result = json.loads(process.stdout)
        self.assertEqual(result["encoding"], "commander")
        self.assertEqual(result["group_size"], 3)
        self.assertEqual(result["status"], "SAT")
        self.assertEqual(result["total_variables"], 36)
        self.assertEqual(result["clauses"], 104)
        self.assertTrue(validate_positions(result["positions"], 4))

    def test_commander_print_board_and_group_size(self) -> None:
        process = self._run_cli("--encoding", "commander", "--n", "4", "--print-board")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Encoding: Commander", process.stdout)
        self.assertIn("Group size: 3", process.stdout)
        board = [line.split() for line in process.stdout.splitlines()[-4:]]
        self.assertTrue(all(len(row) == 4 for row in board))
        positions = [
            (row, col) for row in range(4) for col in range(4) if board[row][col] == "Q"
        ]
        self.assertTrue(validate_positions(positions, 4))

    def test_commander_unsat(self) -> None:
        process = self._run_cli("--encoding", "commander", "--n", "3", "--json")
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIsNone(result["positions"])
        self.assertIsNone(result["valid"])

    def test_old_encodings_remain_selectable_and_default_is_pairwise(self) -> None:
        for encoding_args, expected, clauses in (
            ((), "pairwise", 84),
            (("--encoding", "pairwise"), "pairwise", 84),
            (("--encoding", "binary"), "binary", 120),
            (("--encoding", "sequential"), "sequential", 116),
        ):
            with self.subTest(encoding_args=encoding_args):
                process = self._run_cli(*encoding_args, "--n", "4", "--json")
                self.assertEqual(process.returncode, 0, process.stderr)
                result = json.loads(process.stdout)
                self.assertEqual(result["encoding"], expected)
                self.assertEqual(result["clauses"], clauses)
                self.assertNotIn("group_size", result)
                self.assertTrue(validate_positions(result["positions"], 4))

    def test_invalid_n(self) -> None:
        process = self._run_cli("--encoding", "commander", "--n", "0", "--json")
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(json.loads(process.stdout)["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
