"""Check recursive Commander structure, counts, validation and SAT semantics."""

from itertools import product
import unittest

from pysat.solvers import Glucose3

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.commander import (
    encode_amo_commander,
    encode_exactly_one_commander,
    encode_nqueens_commander,
)
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


def reference_amo_counts(m: int, group_size: int = 3) -> tuple[int, int]:
    """Count the specified Commander variant independently of the encoder."""
    if m <= 1:
        return 0, 0
    if m <= group_size:
        return 0, m * (m - 1) // 2
    sizes = [
        min(group_size, m - start)
        for start in range(0, m, group_size)
    ]
    recursive_aux, recursive_clauses = reference_amo_counts(len(sizes), group_size)
    local_pairwise = sum(size * (size - 1) // 2 for size in sizes)
    return (
        len(sizes) + recursive_aux,
        m + local_pairwise + recursive_clauses,
    )


def reference_nqueens_counts(n: int) -> tuple[int, int]:
    """Sum independent per-group counts, including row/column ALO clauses."""
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
            group_aux, group_clauses = reference_amo_counts(len(group))
            auxiliaries += group_aux
            clauses += group_clauses + int(exactly_one)
    return auxiliaries, clauses


class TestCommanderCardinality(unittest.TestCase):
    def _encode_size(self, m: int) -> tuple[list[list[int]], AuxiliaryVariableAllocator]:
        allocator = AuxiliaryVariableAllocator(max(1, m + 1))
        clauses = encode_amo_commander(list(range(1, m + 1)), allocator)
        return clauses, allocator

    def test_base_group_sizes(self) -> None:
        expected = {
            0: (0, 0),
            1: (0, 0),
            2: (0, 1),
            3: (0, 3),
        }
        for m, (auxiliaries, clause_count) in expected.items():
            with self.subTest(m=m):
                clauses, allocator = self._encode_size(m)
                self.assertEqual(allocator.allocated_count, auxiliaries)
                self.assertEqual(len(clauses), clause_count)
        self.assertEqual(self._encode_size(0)[0], [])
        self.assertEqual(self._encode_size(1)[0], [])
        self.assertEqual(self._encode_size(2)[0], [[-1, -2]])
        self.assertEqual(
            self._encode_size(3)[0],
            [[-1, -2], [-1, -3], [-2, -3]],
        )

    def test_size_four_exact_clause_order_and_singleton_commander(self) -> None:
        clauses, allocator = self._encode_size(4)
        self.assertEqual(allocator.allocated_count, 2)
        self.assertEqual(
            clauses,
            [
                [-1, -2], [-1, -3], [-2, -3],
                [-1, 5], [-2, 5], [-3, 5],
                [-4, 6],
                [-5, -6],
            ],
        )

    def test_required_recursive_counts(self) -> None:
        expected = {
            5: (2, 10),
            6: (2, 13),
            7: (3, 16),
            10: (6, 27),
        }
        for m, (auxiliaries, clause_count) in expected.items():
            with self.subTest(m=m):
                clauses, allocator = self._encode_size(m)
                self.assertEqual(allocator.allocated_count, auxiliaries)
                self.assertEqual(len(clauses), clause_count)
                self.assertEqual((auxiliaries, clause_count), reference_amo_counts(m))

    def test_size_ten_allocates_two_recursive_levels(self) -> None:
        clauses, allocator = self._encode_size(10)
        used_auxiliaries = {
            abs(lit) for clause in clauses for lit in clause if abs(lit) > 10
        }
        self.assertEqual(used_auxiliaries, set(range(11, 17)))
        self.assertEqual(allocator.next_id, 17)
        self.assertEqual(clauses[-1], [-15, -16])

    def test_exactly_one(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        clauses = encode_exactly_one_commander([1, 2, 3, 4], allocator)
        self.assertEqual(clauses[0], [1, 2, 3, 4])
        self.assertEqual(len(clauses), 9)
        self.assertEqual(allocator.allocated_count, 2)
        singleton_allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(
            encode_exactly_one_commander([1], singleton_allocator), [[1]]
        )
        self.assertEqual(singleton_allocator.allocated_count, 0)

    def test_exactly_one_rejects_empty(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        with self.assertRaises(ValueError):
            encode_exactly_one_commander([], allocator)
        self.assertEqual(allocator.allocated_count, 0)

    def test_invalid_variable_ids_do_not_allocate(self) -> None:
        invalid_inputs = (
            [0], [-1], [1, 1], [1, 0], [True], [False], [1.0], ["1"],
            [None], [[1]], None, 1, "1234", (1, 2, 3, 4),
        )
        for encode in (encode_amo_commander, encode_exactly_one_commander):
            for variables in invalid_inputs:
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(30)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.next_id, 30)

    def test_invalid_group_sizes_and_allocator(self) -> None:
        for group_size in (0, 1, -1, True, False, 2.5, "3", None):
            with self.subTest(group_size=group_size):
                allocator = AuxiliaryVariableAllocator(5)
                with self.assertRaises(ValueError):
                    encode_amo_commander([1, 2, 3, 4], allocator, group_size)
                self.assertEqual(allocator.allocated_count, 0)
        for encode in (encode_amo_commander, encode_exactly_one_commander):
            with self.subTest(encoder=encode.__name__), self.assertRaises(ValueError):
                encode([1, 2, 3, 4], None)

    def test_collision_is_rejected_before_commander_allocation(self) -> None:
        for encode in (encode_amo_commander, encode_exactly_one_commander):
            with self.subTest(encoder=encode.__name__):
                allocator = AuxiliaryVariableAllocator(4)
                with self.assertRaises(ValueError):
                    encode([1, 2, 3, 4], allocator)
                self.assertEqual(allocator.allocated_count, 0)

    def test_previously_allocated_commander_cannot_become_an_original(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        encode_amo_commander([1, 2, 3, 4], allocator)
        with self.assertRaises(ValueError):
            encode_amo_commander([1, 2, 5, 6], allocator)
        self.assertEqual(allocator.allocated_count, 2)

    def test_multiple_groups_use_disjoint_auxiliary_ids(self) -> None:
        allocator = AuxiliaryVariableAllocator(30)
        first = encode_amo_commander([1, 2, 3, 4], allocator)
        second = encode_amo_commander([5, 6, 7, 8, 9, 10, 11], allocator)
        third = encode_amo_commander([12, 13, 14, 15, 16], allocator)
        originals = set(range(1, 17))
        auxiliary_sets = [
            {abs(lit) for clause in clauses for lit in clause} - originals
            for clauses in (first, second, third)
        ]
        self.assertEqual(auxiliary_sets, [{30, 31}, {32, 33, 34}, {35, 36}])
        self.assertEqual(allocator.allocated_count, 7)
        self.assertEqual(allocator.next_id, 37)

    def test_nonconsecutive_ids_preserve_partition_order(self) -> None:
        clauses = encode_amo_commander(
            [7, 2, 11, 19], AuxiliaryVariableAllocator(20)
        )
        self.assertEqual(
            clauses,
            [
                [-7, -2], [-7, -11], [-2, -11],
                [-7, 20], [-2, 20], [-11, 20],
                [-19, 21],
                [-20, -21],
            ],
        )

    def test_inputs_are_not_mutated_or_aliased(self) -> None:
        for encode in (encode_amo_commander, encode_exactly_one_commander):
            with self.subTest(encoder=encode.__name__):
                variables = [7, 2, 11, 19]
                clauses = encode(variables, AuxiliaryVariableAllocator(20))
                self.assertEqual(variables, [7, 2, 11, 19])
                clauses[0].append(99)
                self.assertEqual(variables, [7, 2, 11, 19])


class TestCommanderSemantics(unittest.TestCase):
    def _check_assignments(self, variables: list[int], exactly_one: bool) -> None:
        allocator = AuxiliaryVariableAllocator(max(variables) + 1)
        encode = encode_exactly_one_commander if exactly_one else encode_amo_commander
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

    def test_size_ten_singleton_tail_and_recursive_level(self) -> None:
        variables = list(range(1, 11))
        self._check_assignments(variables, exactly_one=False)
        self._check_assignments(variables, exactly_one=True)


class TestNQueensCommanderEncoding(unittest.TestCase):
    def test_n1_no_auxiliaries_and_no_deduplication(self) -> None:
        self.assertEqual(encode_nqueens_commander(1), ([[1], [1]], 1))

    def test_n4_counts_and_variable_range(self) -> None:
        cnf, total = encode_nqueens_commander(4)
        self.assertEqual(total, 36)
        self.assertEqual(total - 16, 20)
        self.assertEqual(len(cnf), 104)
        self.assertEqual(max(abs(lit) for clause in cnf for lit in clause), 36)
        self.assertEqual({abs(lit) for clause in cnf for lit in clause}, set(range(1, 37)))
        self.assertTrue(all(cnf))

    def test_n4_group_order_and_singleton_commanders(self) -> None:
        cnf, _ = encode_nqueens_commander(4)
        self.assertEqual(cnf[:9], [
            [1, 2, 3, 4],
            [-1, -2], [-1, -3], [-2, -3],
            [-1, 17], [-2, 17], [-3, 17], [-4, 18], [-17, -18],
        ])
        self.assertEqual(cnf[36:45], [
            [1, 5, 9, 13],
            [-1, -5], [-1, -9], [-5, -9],
            [-1, 25], [-5, 25], [-9, 25], [-13, 26], [-25, -26],
        ])
        self.assertEqual(len(cnf[:72]), 72)
        self.assertEqual(len(cnf[72:88]), 16)
        self.assertEqual(len(cnf[88:]), 16)

    def test_only_rows_and_columns_have_alo(self) -> None:
        cnf, _ = encode_nqueens_commander(4)
        alo = [clause for clause in cnf if all(lit > 0 for lit in clause)]
        self.assertEqual(alo, all_rows(4) + all_columns(4))
        self.assertTrue(all(len(clause) == 2 for clause in cnf[72:]))

    def test_reference_counts_for_required_board_sizes(self) -> None:
        expected = {
            1: (0, 1, 2),
            4: (20, 36, 104),
            20: (772, 1_172, 4_278),
            50: (5_014, 7_514, 28_726),
            100: (20_536, 30_536, 118_092),
        }
        for n, (auxiliaries, total, clause_count) in expected.items():
            with self.subTest(n=n):
                reference_aux, reference_clauses = reference_nqueens_counts(n)
                self.assertEqual((reference_aux, reference_clauses), (auxiliaries, clause_count))
                cnf, actual_total = encode_nqueens_commander(n)
                self.assertEqual(actual_total, total)
                self.assertEqual(len(cnf), clause_count)

    def test_deterministic(self) -> None:
        self.assertEqual(encode_nqueens_commander(8), encode_nqueens_commander(8))

    def test_invalid_n_and_group_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                encode_nqueens_commander(n)
        for group_size in (0, 1, True, 2.5):
            with self.subTest(group_size=group_size), self.assertRaises(ValueError):
                encode_nqueens_commander(4, group_size)


if __name__ == "__main__":
    unittest.main()
