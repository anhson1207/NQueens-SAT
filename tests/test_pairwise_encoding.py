"""Test Pairwise CNF construction without invoking a SAT solver."""

import unittest

from src.sat.encodings.pairwise import (
    encode_alo,
    encode_amo_pairwise,
    encode_exactly_one_pairwise,
    encode_nqueens_pairwise,
)


class TestCardinalityEncodings(unittest.TestCase):
    def test_alo(self) -> None:
        self.assertEqual(encode_alo([1, 2, 3, 4]), [[1, 2, 3, 4]])

    def test_amo_three_variables(self) -> None:
        self.assertEqual(
            encode_amo_pairwise([1, 2, 3]),
            [[-1, -2], [-1, -3], [-2, -3]],
        )

    def test_amo_four_variables(self) -> None:
        clauses = encode_amo_pairwise([1, 2, 3, 4])
        self.assertEqual(
            clauses,
            [[-1, -2], [-1, -3], [-1, -4], [-2, -3], [-2, -4], [-3, -4]],
        )
        self.assertEqual(len(clauses), 6)

    def test_exactly_one_three_variables(self) -> None:
        clauses = encode_exactly_one_pairwise([1, 2, 3])
        self.assertEqual(clauses, [[1, 2, 3], [-1, -2], [-1, -3], [-2, -3]])
        self.assertEqual(len(clauses), 4)

    def test_amo_single_variable(self) -> None:
        self.assertEqual(encode_amo_pairwise([1]), [])

    def test_amo_empty(self) -> None:
        self.assertEqual(encode_amo_pairwise([]), [])

    def test_alo_single_variable(self) -> None:
        self.assertEqual(encode_alo([1]), [[1]])

    def test_exactly_one_single_variable(self) -> None:
        self.assertEqual(encode_exactly_one_pairwise([1]), [[1]])

    def test_alo_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            encode_alo([])

    def test_exactly_one_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            encode_exactly_one_pairwise([])

    def test_duplicate_ids_are_rejected(self) -> None:
        for encode in (encode_alo, encode_amo_pairwise, encode_exactly_one_pairwise):
            for variables in ([1, 1, 2], [1, 2, 2]):
                with self.subTest(encoder=encode.__name__, variables=variables):
                    with self.assertRaises(ValueError):
                        encode(variables)

    def test_zero_and_negative_ids_are_rejected(self) -> None:
        for encode in (encode_alo, encode_amo_pairwise, encode_exactly_one_pairwise):
            for variables in ([0, 1, 2], [-1, 2, 3], [0], [-1]):
                with self.subTest(encoder=encode.__name__, variables=variables):
                    with self.assertRaises(ValueError):
                        encode(variables)

    def test_non_integer_ids_are_rejected(self) -> None:
        for encode in (encode_alo, encode_amo_pairwise, encode_exactly_one_pairwise):
            for invalid in (1.0, "1", None, [1]):
                with self.subTest(encoder=encode.__name__, invalid=invalid):
                    with self.assertRaises(ValueError):
                        encode([invalid, 2])

    def test_boolean_ids_are_rejected(self) -> None:
        # bool is an int subclass in Python, but is not a SAT variable ID.
        for encode in (encode_alo, encode_amo_pairwise, encode_exactly_one_pairwise):
            for invalid in (True, False):
                with self.subTest(encoder=encode.__name__, invalid=invalid):
                    with self.assertRaises(ValueError):
                        encode([invalid])

    def test_nonconsecutive_ids_preserve_input_order(self) -> None:
        variables = [7, 2, 11]
        self.assertEqual(encode_alo(variables), [[7, 2, 11]])
        self.assertEqual(
            encode_amo_pairwise(variables), [[-7, -2], [-7, -11], [-2, -11]]
        )
        self.assertEqual(
            encode_exactly_one_pairwise(variables),
            [[7, 2, 11], [-7, -2], [-7, -11], [-2, -11]],
        )

    def test_encoders_do_not_mutate_or_alias_input(self) -> None:
        for encode in (encode_alo, encode_amo_pairwise, encode_exactly_one_pairwise):
            with self.subTest(encoder=encode.__name__):
                variables = [7, 2, 11]
                clauses = encode(variables)
                self.assertEqual(variables, [7, 2, 11])
                clauses[0].append(99)
                self.assertEqual(variables, [7, 2, 11])


class TestNQueensPairwiseEncoding(unittest.TestCase):
    def test_n4_clause_count(self) -> None:
        self.assertEqual(len(encode_nqueens_pairwise(4)), 84)

    def test_small_board_clause_counts(self) -> None:
        for n, expected in ((1, 2), (2, 10), (3, 34), (8, 744)):
            with self.subTest(n=n):
                self.assertEqual(len(encode_nqueens_pairwise(n)), expected)

    def test_n4_variable_range_without_auxiliary_variables(self) -> None:
        cnf = encode_nqueens_pairwise(4)
        ids = [abs(literal) for clause in cnf for literal in clause]
        self.assertTrue(all(1 <= variable <= 16 for variable in ids))
        self.assertEqual(max(ids), 16)
        self.assertEqual(set(ids), set(range(1, 17)))

    def test_n4_row_zero_clauses_come_first(self) -> None:
        self.assertEqual(
            encode_nqueens_pairwise(4)[:7],
            [
                [1, 2, 3, 4],
                [-1, -2], [-1, -3], [-1, -4],
                [-2, -3], [-2, -4], [-3, -4],
            ],
        )

    def test_n4_column_clauses_follow_rows(self) -> None:
        self.assertEqual(
            encode_nqueens_pairwise(4)[28:35],
            [
                [1, 5, 9, 13],
                [-1, -5], [-1, -9], [-1, -13],
                [-5, -9], [-5, -13], [-9, -13],
            ],
        )

    def test_n4_main_diagonal_clauses_follow_columns(self) -> None:
        self.assertEqual(
            encode_nqueens_pairwise(4)[56:70],
            [
                [-3, -8],
                [-2, -7], [-2, -12], [-7, -12],
                [-1, -6], [-1, -11], [-1, -16],
                [-6, -11], [-6, -16], [-11, -16],
                [-5, -10], [-5, -15], [-10, -15],
                [-9, -14],
            ],
        )

    def test_n4_anti_diagonal_clauses_come_last(self) -> None:
        self.assertEqual(
            encode_nqueens_pairwise(4)[70:],
            [
                [-2, -5],
                [-3, -6], [-3, -9], [-6, -9],
                [-4, -7], [-4, -10], [-4, -13],
                [-7, -10], [-7, -13], [-10, -13],
                [-8, -11], [-8, -14], [-11, -14],
                [-12, -15],
            ],
        )

    def test_n4_only_rows_and_columns_have_alo_clauses(self) -> None:
        cnf = encode_nqueens_pairwise(4)
        positive_clauses = [clause for clause in cnf if all(lit > 0 for lit in clause)]
        self.assertEqual(
            positive_clauses,
            [
                [1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16],
                [1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15], [4, 8, 12, 16],
            ],
        )
        self.assertNotIn([1, 6, 11, 16], cnf)
        self.assertNotIn([4, 7, 10, 13], cnf)
        self.assertTrue(
            all(len(clause) == 2 and all(lit < 0 for lit in clause) for clause in cnf[56:])
        )

    def test_n2_complete_clause_order(self) -> None:
        self.assertEqual(
            encode_nqueens_pairwise(2),
            [
                [1, 2], [-1, -2], [3, 4], [-3, -4],
                [1, 3], [-1, -3], [2, 4], [-2, -4],
                [-1, -4], [-2, -3],
            ],
        )

    def test_n1_preserves_duplicate_unit_clauses(self) -> None:
        cnf = encode_nqueens_pairwise(1)
        self.assertEqual(cnf, [[1], [1]])
        self.assertEqual(len(cnf), 2)

    def test_invalid_board_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    encode_nqueens_pairwise(n)


if __name__ == "__main__":
    unittest.main()
