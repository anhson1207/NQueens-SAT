"""Cross-check all SAT encodings through their shared Glucose3 pipeline."""

import unittest

from experiments.configs import (
    CORRECTNESS_N_VALUES,
    EXPECTED_STATUS,
    EXPECTED_STRUCTURE,
    REQUIRED_GLUCOSE3_STATISTICS,
    REQUIRED_RESULT_FIELDS,
    SAT_ENCODINGS,
)
from src.common.validator import validate_positions
from src.sat.encodings.binary import encode_nqueens_binary
from src.sat.encodings.commander import encode_nqueens_commander
from src.sat.encodings.pairwise import encode_nqueens_pairwise
from src.sat.encodings.product import encode_nqueens_product
from src.sat.encodings.sequential import encode_nqueens_sequential
from src.sat.model import var_id
from src.sat.solver import (
    solve_nqueens_binary,
    solve_nqueens_commander,
    solve_nqueens_pairwise,
    solve_nqueens_product,
    solve_nqueens_sequential,
)


SOLVERS = {
    "pairwise": solve_nqueens_pairwise,
    "binary": solve_nqueens_binary,
    "sequential": solve_nqueens_sequential,
    "commander": solve_nqueens_commander,
    "product": solve_nqueens_product,
}


def encode(encoding: str, n: int) -> tuple[list[list[int]], int]:
    encoders = {
        "binary": encode_nqueens_binary,
        "sequential": encode_nqueens_sequential,
        "commander": encode_nqueens_commander,
        "product": encode_nqueens_product,
    }
    if encoding == "pairwise":
        return encode_nqueens_pairwise(n), n * n
    return encoders[encoding](n)


class TestAllEncodingsConsistency(unittest.TestCase):
    def test_primary_mapping_is_shared(self) -> None:
        for n in CORRECTNESS_N_VALUES:
            with self.subTest(n=n):
                self.assertEqual(
                    [var_id(row, col, n) for row in range(n) for col in range(n)],
                    list(range(1, n * n + 1)),
                )

    def test_structural_regression_n4_and_literal_ranges(self) -> None:
        n = 4
        for encoding in SAT_ENCODINGS:
            with self.subTest(encoding=encoding):
                cnf, total = encode(encoding, n)
                primary, auxiliary, expected_total, clauses = EXPECTED_STRUCTURE[(n, encoding)]
                self.assertEqual(primary, n * n)
                self.assertEqual(auxiliary, total - n * n)
                self.assertEqual(total, expected_total)
                self.assertEqual(len(cnf), clauses)
                self.assertTrue(all(clause for clause in cnf))
                literal_ids = {abs(literal) for clause in cnf for literal in clause}
                self.assertNotIn(0, literal_ids)
                self.assertTrue(all(variable <= total for variable in literal_ids))
                self.assertTrue(set(range(1, n * n + 1)).issubset(literal_ids))
                self.assertEqual(
                    {variable for variable in literal_ids if variable > n * n},
                    set(range(n * n + 1, total + 1)),
                )

    def test_status_decode_and_validation_for_all_small_instances(self) -> None:
        for n in CORRECTNESS_N_VALUES:
            results = []
            for encoding in SAT_ENCODINGS:
                with self.subTest(n=n, encoding=encoding):
                    result = SOLVERS[encoding](n)
                    results.append(result)
                    self.assertEqual(result["solver"], "Glucose3")
                    self.assertEqual(result["encoding"], encoding)
                    self.assertEqual(result["status"], EXPECTED_STATUS[n], result["error"])
                    self.assertEqual(result["primary_variables"], n * n)
                    self.assertTrue(REQUIRED_RESULT_FIELDS.issubset(result))
                    if EXPECTED_STATUS[n] == "SAT":
                        self.assertIs(result["has_solution"], True)
                        self.assertIs(result["valid"], True)
                        self.assertEqual(len(result["positions"]), n)
                        self.assertTrue(validate_positions(result["positions"], n))
                    else:
                        self.assertIs(result["has_solution"], False)
                        self.assertIsNone(result["positions"])
                        self.assertIsNone(result["valid"])
            self.assertEqual({result["status"] for result in results}, {EXPECTED_STATUS[n]})

    def test_schema_timing_statistics_and_legacy_phase_metadata(self) -> None:
        results = {encoding: SOLVERS[encoding](4) for encoding in SAT_ENCODINGS}
        common_keys = set(results["pairwise"])
        for encoding, result in results.items():
            with self.subTest(encoding=encoding):
                expected_keys = common_keys | ({"group_size"} if encoding == "commander" else set())
                self.assertEqual(set(result), expected_keys)
                self.assertEqual(result["phase_policy"], "legacy")
                if encoding == "product":
                    self.assertEqual(result["phase_override"], "deterministic_aux_pattern")
                    self.assertEqual(result["phase_literals"], result["auxiliary_variables"])
                else:
                    self.assertEqual(result["phase_override"], "solver_default")
                    self.assertEqual(result["phase_literals"], 0)
                self.assertEqual(
                    result["solve_time"], result["load_time"] + result["search_time"]
                )
                for key in (
                    "encoding_time",
                    "load_time",
                    "configuration_time",
                    "search_time",
                    "solve_time",
                    "decode_validate_time",
                    "total_time",
                ):
                    self.assertGreaterEqual(result[key], 0.0)
                measured = sum(
                    result[key]
                    for key in (
                        "encoding_time",
                        "load_time",
                        "configuration_time",
                        "search_time",
                        "decode_validate_time",
                    )
                )
                self.assertGreaterEqual(result["total_time"], measured)
                self.assertTrue(REQUIRED_GLUCOSE3_STATISTICS.issubset(result["statistics"]))


if __name__ == "__main__":
    unittest.main()
