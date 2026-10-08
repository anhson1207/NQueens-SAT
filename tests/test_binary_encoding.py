"""Check Binary structure and existential semantics without using a SAT solver."""

from itertools import product
import unittest

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.binary import (
    encode_amo_binary,
    encode_exactly_one_binary,
    encode_nqueens_binary,
)
from src.sat.model import all_columns, all_rows


class TestAuxiliaryVariableAllocator(unittest.TestCase):
    def test_initial_state_and_consecutive_unique_ids(self) -> None:
        allocator = AuxiliaryVariableAllocator(17)
        self.assertEqual(allocator.next_id, 17)
        self.assertEqual(allocator.allocated_count, 0)
        self.assertEqual([allocator.new_var() for _ in range(4)], [17, 18, 19, 20])
        self.assertEqual(allocator.next_id, 21)
        self.assertEqual(allocator.allocated_count, 4)

    def test_start_at_one(self) -> None:
        self.assertEqual(AuxiliaryVariableAllocator(1).new_var(), 1)

    def test_invalid_start_ids(self) -> None:
        for start in (0, -1, True, False, 1.5, "1", None):
            with self.subTest(start=start), self.assertRaises(ValueError):
                AuxiliaryVariableAllocator(start)


class TestBinaryCardinality(unittest.TestCase):
    def test_amo_empty(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        self.assertEqual(encode_amo_binary([], allocator), [])
        self.assertEqual(allocator.allocated_count, 0)

    def test_amo_singleton(self) -> None:
        allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(encode_amo_binary([1], allocator), [])
        self.assertEqual(allocator.allocated_count, 0)

    def test_amo_size_two(self) -> None:
        allocator = AuxiliaryVariableAllocator(3)
        self.assertEqual(encode_amo_binary([1, 2], allocator), [[-1, -3], [-2, 3]])
        self.assertEqual(allocator.allocated_count, 1)

    def test_amo_size_three(self) -> None:
        allocator = AuxiliaryVariableAllocator(4)
        self.assertEqual(
            encode_amo_binary([1, 2, 3], allocator),
            [[-1, -4], [-1, -5], [-2, 4], [-2, -5], [-3, -4], [-3, 5]],
        )
        self.assertEqual(allocator.allocated_count, 2)

    def test_amo_size_four_lowest_bit_first(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        self.assertEqual(
            encode_amo_binary([1, 2, 3, 4], allocator),
            [
                [-1, -5], [-1, -6], [-2, 5], [-2, -6],
                [-3, -5], [-3, 6], [-4, 5], [-4, 6],
            ],
        )
        self.assertEqual(allocator.allocated_count, 2)

    def test_exactly_one_size_four(self) -> None:
        allocator = AuxiliaryVariableAllocator(5)
        clauses = encode_exactly_one_binary([1, 2, 3, 4], allocator)
        self.assertEqual(clauses[0], [1, 2, 3, 4])
        self.assertEqual(len(clauses), 9)
        self.assertEqual(allocator.allocated_count, 2)
        self.assertEqual(
            clauses[1:], encode_amo_binary([1, 2, 3, 4], AuxiliaryVariableAllocator(5))
        )

    def test_exactly_one_singleton(self) -> None:
        allocator = AuxiliaryVariableAllocator(2)
        self.assertEqual(encode_exactly_one_binary([1], allocator), [[1]])
        self.assertEqual(allocator.allocated_count, 0)

    def test_exactly_one_rejects_empty(self) -> None:
        allocator = AuxiliaryVariableAllocator(1)
        with self.assertRaises(ValueError):
            encode_exactly_one_binary([], allocator)
        self.assertEqual(allocator.allocated_count, 0)

    def test_invalid_variables_do_not_consume_ids(self) -> None:
        invalid_inputs = (
            [0], [-1], [1, 1], [1, 0], [True], [False], [1.0], ["1"],
            [None], [[1]], None, 1, "12", (1, 2),
        )
        for encode in (encode_amo_binary, encode_exactly_one_binary):
            for variables in invalid_inputs:
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(10)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.next_id, 10)

    def test_rejects_collisions_before_allocating(self) -> None:
        for encode in (encode_amo_binary, encode_exactly_one_binary):
            for variables in ([1, 3], [1, 10]):
                with self.subTest(encoder=encode.__name__, variables=variables):
                    allocator = AuxiliaryVariableAllocator(3)
                    with self.assertRaises(ValueError):
                        encode(variables, allocator)
                    self.assertEqual(allocator.allocated_count, 0)

    def test_previously_allocated_auxiliary_cannot_be_an_original(self) -> None:
        allocator = AuxiliaryVariableAllocator(3)
        encode_amo_binary([1, 2], allocator)
        with self.assertRaises(ValueError):
            encode_amo_binary([1, 3], allocator)
        self.assertEqual(allocator.allocated_count, 1)

    def test_consecutive_groups_use_disjoint_auxiliaries(self) -> None:
        allocator = AuxiliaryVariableAllocator(11)
        first = encode_amo_binary([1, 2, 3, 4], allocator)
        second = encode_amo_binary([4, 5, 6], allocator)
        third = encode_amo_binary([1, 10], allocator)
        self.assertEqual({abs(clause[1]) for clause in first}, {11, 12})
        self.assertEqual({abs(clause[1]) for clause in second}, {13, 14})
        self.assertEqual({abs(clause[1]) for clause in third}, {15})
        self.assertEqual(allocator.allocated_count, 5)
        self.assertEqual(allocator.next_id, 16)

    def test_nonconsecutive_unsorted_ids_use_list_indices(self) -> None:
        self.assertEqual(
            encode_amo_binary([7, 2, 11], AuxiliaryVariableAllocator(12)),
            [[-7, -12], [-7, -13], [-2, 12], [-2, -13], [-11, -12], [-11, 13]],
        )

    def test_inputs_are_not_mutated_or_aliased(self) -> None:
        for encode in (encode_amo_binary, encode_exactly_one_binary):
            with self.subTest(encoder=encode.__name__):
                variables = [7, 2, 11]
                clauses = encode(variables, AuxiliaryVariableAllocator(12))
                self.assertEqual(variables, [7, 2, 11])
                clauses[0].append(99)
                self.assertEqual(variables, [7, 2, 11])


class TestBinaryExistentialSemantics(unittest.TestCase):
    def _check_all_assignments(self, exactly_one: bool) -> None:
        encode = encode_exactly_one_binary if exactly_one else encode_amo_binary
        for m in range(1, 6):
            allocator = AuxiliaryVariableAllocator(m + 1)
            cnf = encode(list(range(1, m + 1)), allocator)
            for primary_values in product((False, True), repeat=m):
                with self.subTest(m=m, primary_values=primary_values):
                    satisfiable = False
                    for auxiliary_values in product(
                        (False, True), repeat=allocator.allocated_count
                    ):
                        # Index zero is unused: values are indexed by SAT IDs.
                        values = (False,) + primary_values + auxiliary_values
                        if all(
                            any(values[abs(lit)] == (lit > 0) for lit in clause)
                            for clause in cnf
                        ):
                            satisfiable = True
                            break
                    expected = (
                        sum(primary_values) == 1 if exactly_one else sum(primary_values) <= 1
                    )
                    self.assertEqual(satisfiable, expected)

    def test_amo_exhaustive_primary_and_existential_auxiliary_assignments(self) -> None:
        self._check_all_assignments(exactly_one=False)

    def test_exactly_one_exhaustive_primary_and_existential_auxiliary_assignments(self) -> None:
        self._check_all_assignments(exactly_one=True)


class TestNQueensBinaryEncoding(unittest.TestCase):
    def test_n4_counts_and_variable_range(self) -> None:
        cnf, total = encode_nqueens_binary(4)
        self.assertEqual(total, 48)
        self.assertEqual(total - 16, 32)
        self.assertEqual(len(cnf), 120)
        self.assertEqual(max(abs(lit) for clause in cnf for lit in clause), 48)
        self.assertEqual({abs(lit) for clause in cnf for lit in clause}, set(range(1, 49)))
        self.assertTrue(all(cnf))

    def test_n4_group_order_and_independent_bits(self) -> None:
        cnf, _ = encode_nqueens_binary(4)
        self.assertEqual(cnf[:3], [[1, 2, 3, 4], [-1, -17], [-1, -18]])
        self.assertEqual(cnf[36:39], [[1, 5, 9, 13], [-1, -25], [-1, -26]])
        self.assertEqual(cnf[72:74], [[-3, -33], [-8, 33]])
        self.assertEqual(cnf[96:98], [[-2, -41], [-5, 41]])
        self.assertEqual(len(cnf[:72]), 72)
        self.assertEqual(len(cnf[72:96]), 24)
        self.assertEqual(len(cnf[96:]), 24)

    def test_only_rows_and_columns_have_alo(self) -> None:
        cnf, _ = encode_nqueens_binary(4)
        alo = [clause for clause in cnf if all(lit > 0 for lit in clause)]
        self.assertEqual(alo, all_rows(4) + all_columns(4))
        self.assertTrue(all(len(clause) == 2 and clause[0] < 0 for clause in cnf[72:]))

    def test_n1_no_auxiliaries_and_no_deduplication(self) -> None:
        self.assertEqual(encode_nqueens_binary(1), ([[1], [1]], 1))

    def test_deterministic(self) -> None:
        self.assertEqual(encode_nqueens_binary(8), encode_nqueens_binary(8))

    def test_invalid_n(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n), self.assertRaises(ValueError):
                encode_nqueens_binary(n)


if __name__ == "__main__":
    unittest.main()
