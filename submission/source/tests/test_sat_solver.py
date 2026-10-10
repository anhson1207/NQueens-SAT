"""Test SAT model decoding, real small CNFs, and solver status handling."""

from contextlib import redirect_stdout
from io import StringIO
import json
import unittest
from unittest.mock import patch

from src.sat.solver import decode_sat_model, main, solve_cnf


class TestDecodeSATModel(unittest.TestCase):
    def test_signed_assignment(self) -> None:
        model = [
            -1, 2, -3, -4, -5, -6, -7, 8,
            9, -10, -11, -12, -13, -14, 15, -16,
        ]
        self.assertEqual(decode_sat_model(model, 4), [(0, 1), (1, 3), (2, 0), (3, 2)])

    def test_ignores_auxiliaries_and_sorts_without_mutating_model(self) -> None:
        model = [99, 15, -1, 17, 9, 8, 2, -18]
        original = model.copy()
        self.assertEqual(decode_sat_model(model, 4), [(0, 1), (1, 3), (2, 0), (3, 2)])
        self.assertEqual(model, original)

    def test_does_not_complete_partial_assignments(self) -> None:
        self.assertEqual(decode_sat_model([2], 4), [(0, 1)])
        self.assertEqual(decode_sat_model([-1, -2, 17], 4), [])
        self.assertEqual(decode_sat_model([], 4), [])

    def test_primary_variable_boundaries(self) -> None:
        self.assertEqual(decode_sat_model([17, 16, 1], 4), [(0, 0), (3, 3)])
        self.assertEqual(decode_sat_model([1, 2], 1), [(0, 0)])

    def test_invalid_board_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                decode_sat_model([], n)


class TestSolveCNF(unittest.TestCase):
    def test_positive_unit_clause(self) -> None:
        result = solve_cnf(1, [[1]])
        self.assertEqual(result["status"], "SAT")
        self.assertIs(result["has_solution"], True)
        self.assertIs(result["valid"], True)
        self.assertEqual(result["positions"], [(0, 0)])
        self.assertEqual(result["clauses"], 1)
        self.assertIsNone(result["encoding"])
        self.assertEqual(result["encoding_time"], 0.0)
        self.assertIsNone(result["error"])

    def test_contradictory_units(self) -> None:
        result = solve_cnf(1, [[1], [-1]])
        self.assertEqual(result["status"], "UNSAT")
        self.assertIs(result["has_solution"], False)
        self.assertIsNone(result["positions"])
        self.assertIsNone(result["valid"])
        self.assertIsNone(result["error"])

    def test_empty_clause_is_unsat(self) -> None:
        self.assertEqual(solve_cnf(1, [[]])["status"], "UNSAT")

    def test_empty_cnf_does_not_fabricate_a_queen(self) -> None:
        result = solve_cnf(1, [])
        self.assertEqual(result["status"], "ERROR")
        self.assertIs(result["has_solution"], True)
        self.assertIs(result["valid"], False)
        self.assertEqual(result["positions"], [])
        self.assertEqual(result["primary_variables"], 1)
        self.assertEqual(result["auxiliary_variables"], 0)

    def test_infers_variable_range_and_ignores_auxiliary_assignments(self) -> None:
        result = solve_cnf(1, [[1], [3]])
        self.assertEqual(result["status"], "SAT")
        self.assertEqual(result["positions"], [(0, 0)])
        self.assertIs(result["valid"], True)
        self.assertEqual(result["primary_variables"], 1)
        self.assertEqual(result["total_variables"], 3)
        self.assertEqual(result["auxiliary_variables"], 2)

    def test_explicit_reserved_variable_count(self) -> None:
        result = solve_cnf(1, [[1]], total_variables=5)
        self.assertEqual(result["total_variables"], 5)
        self.assertEqual(result["auxiliary_variables"], 4)

    def test_rejects_inconsistent_total_variables(self) -> None:
        for total in (0, 2, True, 3.5):
            with self.subTest(total=total), self.assertRaises(ValueError):
                solve_cnf(1, [[1], [3]], total_variables=total)
        with self.assertRaises(ValueError):
            solve_cnf(4, [[1]], total_variables=15)

    def test_invalid_n_or_solver_name(self) -> None:
        with self.assertRaises(ValueError):
            solve_cnf(0, [[1]])
        with self.assertRaises(ValueError):
            solve_cnf(1, [[1]], solver_name="unsupported")

    def test_sat_assignment_with_attacking_queens_is_error(self) -> None:
        # This CNF is SAT, but its two queens share a diagonal on a 2x2 board.
        result = solve_cnf(2, [[1], [-2], [-3], [4]])
        self.assertEqual(result["status"], "ERROR")
        self.assertIs(result["has_solution"], True)
        self.assertIs(result["valid"], False)
        self.assertEqual(result["positions"], [(0, 0), (1, 1)])
        self.assertIn("validate_positions", result["error"])
        self.assertIn("decoded_queens=2", result["error"])

    def test_consistent_schema_timing_and_real_statistics(self) -> None:
        sat = solve_cnf(1, [[1]])
        unsat = solve_cnf(1, [[1], [-1]])
        self.assertEqual(set(sat), set(unsat))
        for result in (sat, unsat):
            with self.subTest(status=result["status"]):
                for key in (
                    "encoding_time", "load_time", "search_time", "solve_time",
                    "decode_validate_time", "total_time",
                ):
                    self.assertGreaterEqual(result[key], 0.0)
                self.assertEqual(result["solve_time"], result["load_time"] + result["search_time"])
                self.assertGreaterEqual(
                    result["total_time"], result["solve_time"] + result["decode_validate_time"]
                )
                self.assertIsInstance(result["statistics"], dict)
                for value in result["statistics"].values():
                    self.assertGreaterEqual(value, 0)

    def test_does_not_mutate_cnf(self) -> None:
        cnf = [[1], [2, -3]]
        solve_cnf(1, cnf)
        self.assertEqual(cnf, [[1], [2, -3]])


class TestSolverStatusHandling(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch("src.sat.solver.Glucose3")
        self.addCleanup(patcher.stop)
        self.factory = patcher.start()
        self.context = self.factory.return_value
        self.engine = self.context.__enter__.return_value
        self.engine.accum_stats.return_value = {"conflicts": 3, "extra_stat": 7}

    def test_unknown_is_not_unsat_and_does_not_request_model(self) -> None:
        self.engine.solve.return_value = None
        cnf = [[1]]
        result = solve_cnf(1, cnf)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIs(result["has_solution"], False)
        self.assertIsNone(result["positions"])
        self.assertIsNone(result["valid"])
        self.assertEqual(result["statistics"], {"conflicts": 3, "extra_stat": 7})
        self.engine.get_model.assert_not_called()
        self.engine.solve.assert_called_once_with()
        self.assertIs(self.factory.call_args.kwargs["bootstrap_with"], cnf)
        self.context.__exit__.assert_called_once()

    def test_unsat_does_not_request_model_or_validate(self) -> None:
        self.engine.solve.return_value = False
        with patch("src.sat.solver.validate_positions") as validate:
            result = solve_cnf(1, [[1], [-1]])
        self.assertEqual(result["status"], "UNSAT")
        self.engine.get_model.assert_not_called()
        validate.assert_not_called()
        self.engine.solve.assert_called_once_with()
        self.context.__exit__.assert_called_once()

    def test_sat_without_model_is_error(self) -> None:
        self.engine.solve.return_value = True
        self.engine.get_model.return_value = None
        result = solve_cnf(1, [[1]])
        self.assertEqual(result["status"], "ERROR")
        self.assertIs(result["valid"], False)
        self.assertIsNone(result["positions"])
        self.assertIn("did not provide a model", result["error"])

    def test_unavailable_statistics_are_not_fabricated(self) -> None:
        self.engine.solve.return_value = None
        self.engine.accum_stats.return_value = None
        self.assertIsNone(solve_cnf(1, [[1]])["statistics"])

    def test_solver_exception_propagates_and_closes_context(self) -> None:
        self.engine.solve.side_effect = RuntimeError("solver failed")
        with self.assertRaisesRegex(RuntimeError, "solver failed"):
            solve_cnf(1, [[1]])
        self.context.__exit__.assert_called_once()

    def test_json_cli_unknown_and_error_exit_codes(self) -> None:
        for status, model, expected_status, expected_code in (
            (None, None, "UNKNOWN", 2),
            (True, None, "ERROR", 1),
        ):
            with self.subTest(status=expected_status):
                self.engine.solve.return_value = status
                self.engine.get_model.return_value = model
                output = StringIO()
                with redirect_stdout(output):
                    code = main(["--n", "1", "--json"])
                self.assertEqual(code, expected_code)
                self.assertEqual(json.loads(output.getvalue())["status"], expected_status)

    def test_cli_reports_solver_exception_as_json(self) -> None:
        self.engine.solve.side_effect = RuntimeError("solver failed")
        output = StringIO()
        with redirect_stdout(output):
            code = main(["--n", "1", "--json"])
        self.assertEqual(code, 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("solver failed", result["error"])


if __name__ == "__main__":
    unittest.main()
