"""Check 2-Product structure, integer dimensions, validation and SAT semantics."""

from itertools import product
from math import isqrt
import unittest

from pysat.solvers import Glucose3

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.product import (
    encode_amo_product,
    encode_exactly_one_product,
    encode_nqueens_product,
)
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


def reference_product_counts(m: int) -> tuple[int, int]:
    """Count the specified non-recursive 2-Product variant independently."""
    if m <= 1:
        return 0, 0
    floor_root = isqrt(m)
    p = floor_root if floor_root * floor_root == m else floor_root + 1
    q, remainder = divmod(m, p)
    if remainder:
        q += 1
    return p + q, 2 * m + p * (p - 1) // 2 + q * (q - 1) // 2


def reference_nqueens_counts(n: int) -> tuple[int, int]:
    """Sum independent per-group Product counts and row/column ALO clauses."""
    auxiliaries = 0
    clauses = 0
    sections = (
        (all_rows(n), True),
        (all_columns(n), True),
        (all_main_diagonals(n), False),
        (all_anti_diagonals(n), False),
    )
    for groups, exactly_one in sections:
        for group in groups:
            group_aux, group_clauses = reference_product_counts(len(group))
            auxiliaries += group_aux
            clauses += group_clauses + int(exactly_one)
    return auxiliaries, clauses


class TestProductCardinality(unittest.TestCase):
    def _encode_size(self, m: int) -> tuple[list[list[int]], AuxiliaryVariableAllocator]:
        allocator = AuxiliaryVariableAllocator(max(1, m + 1))
        clauses = encode_amo_product(list(range(1, m + 1)), allocator)
        return clauses, allocator

    def test_empty_and_singleton(self) -> None:
        for m in (0, 1):
            with self.subTest(m=m):
                clauses, allocator = self._encode_size(m)
                self.assertEqual(clauses, [])
                self.assertEqual(allocator.allocated_count, 0)

    def test_size_two_keeps_single_column_auxiliary(self) -> None:
        clauses, allocator = self._encode_size(2)
        self.assertEqual(allocator.allocated_count, 3)
        self.assertEqual(
            clauses,
            [[-1, 3], [-1, 5], [-2, 4], [-2, 5], [-3, -4]],
        )

    def test_size_three(self) -> None:
        clauses, allocator = self._encode_size(3)
        self.assertEqual(allocator.allocated_count, 4)
        self.assertEqual(len(clauses), 8)
        self.assertEqual(
            clauses,
            [
                [-1, 4], [-1, 6], [-2, 4], [-2, 7],
                [-3, 5], [-3, 6], [-4, -5], [-6, -7],
            ],
        )

    def test_size_four_exact_clause_order(self) -> None:
        clauses, allocator = self._encode_size(4)
        self.assertEqual(allocator.allocated_count, 4)
        self.assertEqual(
            clauses,
            [
                [-1, 5], [-1, 7],
                [-2, 5], [-2, 8],
                [-3, 6], [-3, 7],
                [-4, 6], [-4, 8],
                [-5, -6],
                [-7, -8],
            ],
        )

    def test_required_non_square_counts(self) -> None:
        expected = {
            5: (5, 14),
            6: (5, 16),
            7: (6, 20),
            8: (6, 22),
        }
        for m, (auxiliaries, clause_count) in expected.items():
            with self.subTest(m=m):
                clauses, allocator = self._encode_size(m)
                self.assertEqual(allocator.allocated_count, auxiliaries)
                self.assertEqual(len(clauses), clause_count)
                self.assertEqual((auxiliaries, clause_count), reference_product_counts(m))

    def test_size_five_maps_only_real_originals(self) -> None:
        clauses, _ = self._encode_size(5)
        implications = clauses[:10]
        self.assertEqual(
            implications,
            [
                [-1, 6], [-1, 9], [-2, 6], [-2, 10],
                [-3, 7], [-3, 9], [-4, 7], [-4, 10],
                [-5, 8], [-5, 9],
            ],
        )
        self.assertEqual({-clause[0] for clause in implications}, set(range(1, 6)))
        self.assertTrue(all(-clause[0] <= 5 for clause in implications))

    def test_exactly_one(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        clauses = encode_exactly_one_product([1, 2, 3, 4], allocator)
        self.assertEqual(clauses[0], [1, 2, 3, 4])
        self.assertEqual(len(clauses), 11)
        self.assertEqual(allocator.allocated_count, 4)
        singleton_allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(encode_exactly_one_product([1], singleton_allocator), [[1]])
        self.assertEqual(singleton_allocator.allocated_count, 0)

    def test_exactly_one_rejects_empty(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        with self.assertRaises(ValueError):
            encode_exactly_one_product([], allocator)
        self.assertEqual(allocator.allocated_count, 0)

    def test_invalid_variables_and_allocator_do_not_allocate(self) -> None:
        invalid_inputs = (
            [0], [-1], [1, 1], [1, 0], [True], [False], [1.0], ["1"],
            [None], [[1]], None, 1, "1234", (1, 2, 3, 4),
        )
        for encode in (encode_amo_product, encode_exactly_one_product):
            for variables in invalid_inputs:
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(30)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.next_id, 30)
            with self.subTest(encoder=encode.__name__), self.assertRaises(ValueError):
                encode([1, 2, 3, 4], None)

    def test_collision_is_rejected_before_allocation(self) -> None:
        for encode in (encode_amo_product, encode_exactly_one_product):
            with self.subTest(encoder=encode.__name__):
                allocator = AuxiliaryVariableAllocator(4)
                with self.assertRaises(ValueError):
                    encode([1, 2, 3, 4], allocator)
                self.assertEqual(allocator.allocated_count, 0)

    def test_previously_allocated_auxiliary_cannot_be_an_original(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        encode_amo_product([1, 2, 3, 4], allocator)
        with self.assertRaises(ValueError):
            encode_amo_product([1, 2, 5, 6], allocator)
        self.assertEqual(allocator.allocated_count, 4)

    def test_multiple_groups_use_disjoint_auxiliary_ids(self) -> None:
        allocator = AuxiliaryVariableAllocator(30)
        first = encode_amo_product([1, 2, 3, 4], allocator)
        second = encode_amo_product([5, 6, 7, 8, 9], allocator)
        third = encode_amo_product([10, 11], allocator)
        originals = set(range(1, 12))
        auxiliary_sets = [
            {abs(lit) for clause in clauses for lit in clause} - originals
            for clauses in (first, second, third)
        ]
        self.assertEqual(
            auxiliary_sets,
            [set(range(30, 34)), set(range(34, 39)), set(range(39, 42))],
        )
        self.assertEqual(allocator.allocated_count, 12)
        self.assertEqual(allocator.next_id, 42)

    def test_nonconsecutive_ids_preserve_row_major_order(self) -> None:
        clauses = encode_amo_product(
            [7, 2, 11, 19], AuxiliaryVariableAllocator(20)
        )
        self.assertEqual(
            clauses,
            [
                [-7, 20], [-7, 22], [-2, 20], [-2, 23],
                [-11, 21], [-11, 22], [-19, 21], [-19, 23],
                [-20, -21], [-22, -23],
            ],
        )

    def test_deterministic_and_input_not_mutated_or_aliased(self) -> None:
        variables = [7, 2, 11, 19, 25]
        first = encode_amo_product(variables, AuxiliaryVariableAllocator(26))
        second = encode_amo_product(variables, AuxiliaryVariableAllocator(26))
        self.assertEqual(first, second)
        self.assertEqual(variables, [7, 2, 11, 19, 25])
        first[0].append(99)
        self.assertEqual(variables, [7, 2, 11, 19, 25])


class TestProductSemantics(unittest.TestCase):
    def _check_assignments(self, variables: list[int], exactly_one: bool) -> None:
        allocator = AuxiliaryVariableAllocator(max(variables) + 1)
        encode = encode_exactly_one_product if exactly_one else encode_amo_product
        cnf = encode(variables, allocator)
        with Glucose3(bootstrap_with=cnf) as solver:
            for values in product((False, True), repeat=len(variables)):
                assumptions = [var if value else -var for var, value in zip(variables, values)]
                with self.subTest(
                    variables=variables, exactly_one=exactly_one, values=values
                ):
                    expected = sum(values) == 1 if exactly_one else sum(values) <= 1
                    self.assertEqual(solver.solve(assumptions=assumptions), expected)

    def test_all_assignments_for_sizes_one_through_seven(self) -> None:
        for m in range(1, 8):
            variables = list(range(1, m + 1))
            self._check_assignments(variables, exactly_one=False)
            self._check_assignments(variables, exactly_one=True)

    def test_nonconsecutive_original_ids(self) -> None:
        variables = [2, 7, 11, 19, 25]
        self._check_assignments(variables, exactly_one=False)
        self._check_assignments(variables, exactly_one=True)

    def test_same_row_same_column_and_different_coordinates_conflict(self) -> None:
        cnf = encode_amo_product([1, 2, 3, 4], AuxiliaryVariableAllocator(5))
        with Glucose3(bootstrap_with=cnf) as solver:
            self.assertFalse(solver.solve(assumptions=[1, 2]))  # same grid row
            self.assertFalse(solver.solve(assumptions=[1, 3]))  # same grid column
            self.assertFalse(solver.solve(assumptions=[1, 4]))  # different row/column
            self.assertTrue(solver.solve(assumptions=[-1, -2, -3, -4]))
            self.assertTrue(solver.solve(assumptions=[1, -2, -3, -4]))


class TestNQueensProductEncoding(unittest.TestCase):
    def test_n1_no_auxiliaries_and_no_deduplication(self) -> None:
        self.assertEqual(encode_nqueens_product(1), ([[1], [1]], 1))

    def test_n4_counts_and_variable_range(self) -> None:
        cnf, total = encode_nqueens_product(4)
        self.assertEqual(total, 84)
        self.assertEqual(total - 16, 68)
        self.assertEqual(len(cnf), 160)
        self.assertEqual(max(abs(lit) for clause in cnf for lit in clause), 84)
        self.assertEqual({abs(lit) for clause in cnf for lit in clause}, set(range(1, 85)))
        self.assertTrue(all(cnf))

    def test_n4_group_order_and_auxiliary_order(self) -> None:
        cnf, _ = encode_nqueens_product(4)
        self.assertEqual(cnf[:11], [
            [1, 2, 3, 4],
            [-1, 17], [-1, 19], [-2, 17], [-2, 20],
            [-3, 18], [-3, 19], [-4, 18], [-4, 20],
            [-17, -18], [-19, -20],
        ])
        self.assertEqual(cnf[44:55], [
            [1, 5, 9, 13],
            [-1, 33], [-1, 35], [-5, 33], [-5, 36],
            [-9, 34], [-9, 35], [-13, 34], [-13, 36],
            [-33, -34], [-35, -36],
        ])
        self.assertEqual(cnf[88:93], [
            [-3, 49], [-3, 51], [-8, 50], [-8, 51], [-49, -50],
        ])
        self.assertEqual(len(cnf[:88]), 88)
        self.assertEqual(len(cnf[88:124]), 36)
        self.assertEqual(len(cnf[124:]), 36)

    def test_only_rows_and_columns_have_alo(self) -> None:
        cnf, _ = encode_nqueens_product(4)
        alo = [clause for clause in cnf if all(lit > 0 for lit in clause)]
        self.assertEqual(alo, all_rows(4) + all_columns(4))
        self.assertTrue(all(len(clause) == 2 for clause in cnf[88:]))

    def test_reference_counts_for_required_board_sizes(self) -> None:
        expected = {
            1: (0, 1, 2),
            4: (68, 84, 160),
            20: (854, 1_254, 4_520),
        }
        for n, (auxiliaries, total, clause_count) in expected.items():
            with self.subTest(n=n):
                reference_aux, reference_clauses = reference_nqueens_counts(n)
                self.assertEqual((reference_aux, reference_clauses), (auxiliaries, clause_count))
                cnf, actual_total = encode_nqueens_product(n)
                self.assertEqual(actual_total, total)
                self.assertEqual(len(cnf), clause_count)

    def test_deterministic(self) -> None:
        self.assertEqual(encode_nqueens_product(8), encode_nqueens_product(8))

    def test_invalid_n(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                encode_nqueens_product(n)


if __name__ == "__main__":
    unittest.main()
