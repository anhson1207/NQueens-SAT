"""Check Sequential Counter structure and semantics on small groups and boards."""

from itertools import product
import unittest

from pysat.solvers import Glucose3

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.sequential import (
    encode_amo_sequential,
    encode_exactly_one_sequential,
    encode_nqueens_sequential,
)
from src.sat.model import all_columns, all_rows


class TestSequentialCardinality(unittest.TestCase):
    def test_amo_empty(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        self.assertEqual(encode_amo_sequential([], allocator), [])
        self.assertEqual(allocator.allocated_count, 0)

    def test_amo_singleton(self) -> None:
        allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(encode_amo_sequential([1], allocator), [])
        self.assertEqual(allocator.allocated_count, 0)

    def test_amo_size_two_uses_sequential_variant(self) -> None:
        allocator = AuxiliaryVariableAllocator(3)
        self.assertEqual(encode_amo_sequential([1, 2], allocator), [[-1, 3], [-2, -3]])
        self.assertEqual(allocator.allocated_count, 1)

    def test_amo_size_three(self) -> None:
        allocator = AuxiliaryVariableAllocator(4)
        self.assertEqual(
            encode_amo_sequential([1, 2, 3], allocator),
            [[-1, 4], [-2, 5], [-4, 5], [-2, -4], [-3, -5]],
        )
        self.assertEqual(allocator.allocated_count, 2)

    def test_amo_size_four_exact_clause_order(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        self.assertEqual(
            encode_amo_sequential([1, 2, 3, 4], allocator),
            [
                [-1, 5],
                [-2, 6], [-5, 6], [-2, -5],
                [-3, 7], [-6, 7], [-3, -6],
                [-4, -7],
            ],
        )
        self.assertEqual(allocator.allocated_count, 3)

    def test_exactly_one_size_four(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        clauses = encode_exactly_one_sequential([1, 2, 3, 4], allocator)
        self.assertEqual(clauses[0], [1, 2, 3, 4])
        self.assertEqual(len(clauses), 9)
        self.assertEqual(allocator.allocated_count, 3)
        self.assertEqual(
            clauses[1:],
            encode_amo_sequential([1, 2, 3, 4], AuxiliaryVariableAllocator(5)),
        )

    def test_exactly_one_singleton(self) -> None:
        allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(encode_exactly_one_sequential([1], allocator), [[1]])
        self.assertEqual(allocator.allocated_count, 0)

    def test_exactly_one_rejects_empty_without_allocating(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        with self.assertRaises(ValueError):
            encode_exactly_one_sequential([], allocator)
        self.assertEqual(allocator.allocated_count, 0)

    def test_invalid_variables_do_not_consume_ids(self) -> None:
        invalid_inputs = (
            [0], [-1], [1, 1], [1, 0], [True], [False], [1.0], ["1"],
            [None], [[1]], None, 1, "12", (1, 2),
        )
        for encode in (encode_amo_sequential, encode_exactly_one_sequential):
            for variables in invalid_inputs:
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(20)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.next_id, 20)

    def test_rejects_original_auxiliary_collision_before_allocating(self) -> None:
        for encode in (encode_amo_sequential, encode_exactly_one_sequential):
            for variables in ([1, 3], [1, 10]):
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(3)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.allocated_count, 0)

    def test_previously_allocated_auxiliary_cannot_be_an_original(self) -> None:
        allocator = AuxiliaryVariableAllocator(3)
        encode_amo_sequential([1, 2], allocator)
        with self.assertRaises(ValueError):
            encode_amo_sequential([1, 3], allocator)
        self.assertEqual(allocator.allocated_count, 1)

    def test_consecutive_groups_have_disjoint_auxiliary_chains(self) -> None:
        allocator = AuxiliaryVariableAllocator(12)
        first = encode_amo_sequential([1, 2, 3, 4], allocator)
        second = encode_amo_sequential([4, 7, 11], allocator)
        third = encode_amo_sequential([2, 10], allocator)
        originals = {1, 2, 3, 4, 7, 10, 11}
        first_aux = {abs(lit) for clause in first for lit in clause} - originals
        second_aux = {abs(lit) for clause in second for lit in clause} - originals
        third_aux = {abs(lit) for clause in third for lit in clause} - originals
        self.assertEqual(first_aux, {12, 13, 14})
        self.assertEqual(second_aux, {15, 16})
        self.assertEqual(third_aux, {17})
        self.assertEqual(allocator.allocated_count, 6)
        self.assertEqual(allocator.next_id, 18)

    def test_nonconsecutive_unsorted_ids_preserve_list_order(self) -> None:
        self.assertEqual(
            encode_amo_sequential([7, 2, 11], AuxiliaryVariableAllocator(12)),
            [[-7, 12], [-2, 13], [-12, 13], [-2, -12], [-11, -13]],
        )

    def test_inputs_are_not_mutated_or_aliased(self) -> None:
        for encode in (encode_amo_sequential, encode_exactly_one_sequential):
            with self.subTest(encoder=encode.__name__):
                variables = [7, 2, 11]
                clauses = encode(variables, AuxiliaryVariableAllocator(12))
                self.assertEqual(variables, [7, 2, 11])
                clauses[0].append(99)
                self.assertEqual(variables, [7, 2, 11])


class TestSequentialSemantics(unittest.TestCase):
    def _check_assignments(self, variables: list[int], exactly_one: bool) -> None:
        allocator = AuxiliaryVariableAllocator(max(variables) + 1)
        encode = encode_exactly_one_sequential if exactly_one else encode_amo_sequential
        cnf = encode(variables, allocator)
        with Glucose3(bootstrap_with=cnf) as solver:
            for values in product((False, True), repeat=len(variables)):
                assumptions = [var if value else -var for var, value in zip(variables, values)]
                with self.subTest(
                    variables=variables, exactly_one=exactly_one, values=values
                ):
                    expected = sum(values) == 1 if exactly_one else sum(values) <= 1
                    self.assertEqual(solver.solve(assumptions=assumptions), expected)

    def test_amo_all_primary_assignments_with_existential_auxiliaries(self) -> None:
        for m in range(1, 6):
            self._check_assignments(list(range(1, m + 1)), exactly_one=False)

    def test_exactly_one_all_primary_assignments_with_existential_auxiliaries(self) -> None:
        for m in range(1, 6):
            self._check_assignments(list(range(1, m + 1)), exactly_one=True)

    def test_nonconsecutive_original_ids(self) -> None:
        self._check_assignments([2, 7, 11], exactly_one=False)
        self._check_assignments([2, 7, 11], exactly_one=True)


class TestNQueensSequentialEncoding(unittest.TestCase):
    def test_n1_no_auxiliaries_and_no_deduplication(self) -> None:
        self.assertEqual(encode_nqueens_sequential(1), ([[1], [1]], 1))

    def test_n4_counts_and_variable_range(self) -> None:
        cnf, total = encode_nqueens_sequential(4)
        self.assertEqual(total, 58)
        self.assertEqual(total - 16, 42)
        self.assertEqual(len(cnf), 116)
        self.assertEqual(max(abs(lit) for clause in cnf for lit in clause), 58)
        self.assertEqual({abs(lit) for clause in cnf for lit in clause}, set(range(1, 59)))
        self.assertTrue(all(cnf))

    def test_n4_group_order_and_fresh_chains(self) -> None:
        cnf, _ = encode_nqueens_sequential(4)
        self.assertEqual(cnf[:9], [
            [1, 2, 3, 4], [-1, 17], [-2, 18], [-17, 18], [-2, -17],
            [-3, 19], [-18, 19], [-3, -18], [-4, -19],
        ])
        self.assertEqual(cnf[36:45], [
            [1, 5, 9, 13], [-1, 29], [-5, 30], [-29, 30], [-5, -29],
            [-9, 31], [-30, 31], [-9, -30], [-13, -31],
        ])
        self.assertEqual(cnf[72:74], [[-3, 41], [-8, -41]])
        self.assertEqual(cnf[94:96], [[-2, 50], [-5, -50]])
        self.assertEqual(len(cnf[:72]), 72)
        self.assertEqual(len(cnf[72:94]), 22)
        self.assertEqual(len(cnf[94:]), 22)

    def test_only_rows_and_columns_have_alo(self) -> None:
        cnf, _ = encode_nqueens_sequential(4)
        alo = [clause for clause in cnf if all(lit > 0 for lit in clause)]
        self.assertEqual(alo, all_rows(4) + all_columns(4))
        self.assertTrue(all(len(clause) == 2 for clause in cnf[72:]))

    def test_general_count_formulas(self) -> None:
        for n in (1, 2, 3, 4, 8, 20):
            with self.subTest(n=n):
                cnf, total = encode_nqueens_sequential(n)
                self.assertEqual(total - n * n, 4 * n * n - 6 * n + 2)
                self.assertEqual(total, 5 * n * n - 6 * n + 2)
                self.assertEqual(len(cnf), 12 * n * n - 22 * n + 12)

    def test_deterministic(self) -> None:
        self.assertEqual(encode_nqueens_sequential(8), encode_nqueens_sequential(8))

    def test_invalid_n(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                encode_nqueens_sequential(n)


if __name__ == "__main__":
    unittest.main()
