"""Inspect one shared N=100 Pairwise CNF in memory without solving it."""

from time import perf_counter
import unittest

from src.sat.encodings.pairwise import encode_nqueens_pairwise
from src.sat.model import var_id


class TestN100PairwiseEncoding(unittest.TestCase):
    n = 100
    cnf: list[list[int]]
    encoding_time: float
    variable_ids: set[int]

    @classmethod
    def setUpClass(cls) -> None:
        start = perf_counter()
        cls.cnf = encode_nqueens_pairwise(cls.n)
        cls.encoding_time = perf_counter() - start
        # Stream literals into the small set of used IDs, not a flattened list.
        cls.variable_ids = {abs(lit) for clause in cls.cnf for lit in clause}

    @classmethod
    def tearDownClass(cls) -> None:
        # The test runner can retain this class; release its large fixture now.
        del cls.cnf
        del cls.variable_ids

    def test_cnf_is_materialized(self) -> None:
        self.assertIsInstance(self.cnf, list)
        self.assertTrue(self.cnf, "CNF must not be empty")
        self.assertTrue(all(isinstance(clause, list) for clause in self.cnf))

    def test_variable_counts_without_auxiliary_variables(self) -> None:
        self.assertEqual(max(abs(lit) for clause in self.cnf for lit in clause), 10000)
        self.assertNotIn(0, self.variable_ids)
        self.assertEqual(self.variable_ids, set(range(1, 10001)))
        self.assertEqual(len(self.variable_ids), 10000)
        self.assertEqual(sum(variable > self.n * self.n for variable in self.variable_ids), 0)

    def test_total_clause_count(self) -> None:
        # Rows: 495100; columns: 495100; each diagonal direction: 328350.
        self.assertEqual(len(self.cnf), 1_646_900)

    def test_clause_structure_and_counts(self) -> None:
        alo_count = 0
        amo_count = 0
        for index, clause in enumerate(self.cnf):
            if not clause:
                self.fail(f"Empty clause at index {index}")
            if clause[0] > 0:
                if len(clause) != self.n or not all(lit > 0 for lit in clause):
                    self.fail(f"Invalid ALO clause at index {index}")
                alo_count += 1
            else:
                if len(clause) != 2 or not all(lit < 0 for lit in clause):
                    self.fail(f"Invalid AMO clause at index {index}")
                amo_count += 1
        self.assertEqual(alo_count, 200)
        self.assertEqual(amo_count, 1_646_700)
        self.assertEqual(alo_count + amo_count, len(self.cnf))

    def test_row_zero_clauses(self) -> None:
        self.assertEqual(self.cnf[0], list(range(1, 101)))
        for expected in ([-1, -2], [-1, -3], [-1, -100], [-99, -100]):
            # A compact failure message avoids dumping the complete CNF.
            self.assertTrue(expected in self.cnf, f"Missing row clause: {expected}")

    def test_main_diagonal_has_amo_without_alo(self) -> None:
        diagonal = [var_id(i, i, self.n) for i in range(self.n)]
        for i, j in ((0, 1), (0, 99), (1, 99)):
            expected = [-var_id(i, i, self.n), -var_id(j, j, self.n)]
            self.assertTrue(expected in self.cnf, f"Missing diagonal clause: {expected}")
        self.assertTrue(diagonal not in self.cnf, "Main diagonal must not have an ALO clause")

    def test_encoding_time_and_summary(self) -> None:
        self.assertGreaterEqual(self.encoding_time, 0.0)
        primary_count = sum(1 <= variable <= self.n * self.n for variable in self.variable_ids)
        auxiliary_count = sum(variable > self.n * self.n for variable in self.variable_ids)
        print(
            f"\nMethod: Pairwise\n"
            f"N: {self.n}\n"
            f"Primary variables: {primary_count}\n"
            f"Auxiliary variables: {auxiliary_count}\n"
            f"Total variables: {len(self.variable_ids)}\n"
            f"Clauses: {len(self.cnf)}\n"
            f"Encoding time: {self.encoding_time:.6f} seconds",
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
