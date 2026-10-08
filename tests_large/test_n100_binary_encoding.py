"""Inspect one N=100 Binary CNF, including every group's auxiliary ownership."""

from collections import Counter
import unittest

from src.sat.encodings.binary import encode_nqueens_binary
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


class TestN100BinaryEncoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cnf, cls.total_variables = encode_nqueens_binary(100)

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.cnf

    def test_counts(self) -> None:
        self.assertEqual(self.total_variables, 13_678)
        self.assertEqual(self.total_variables - 10_000, 3_678)
        self.assertEqual(len(self.cnf), 269_024)

    def test_literal_ranges_and_nonempty_clauses(self) -> None:
        self.assertTrue(all(self.cnf), "CNF contains an empty clause")
        self.assertTrue(all(
            isinstance(lit, int) and not isinstance(lit, bool) and 1 <= abs(lit) <= 13_678
            for clause in self.cnf for lit in clause
        ))
        used_ids = {abs(lit) for clause in self.cnf for lit in clause}
        self.assertEqual(used_ids, set(range(1, 13_679)))
        self.assertEqual(min(var for var in used_ids if var > 10_000), 10_001)

    def test_each_group_has_private_bits_and_expected_clauses(self) -> None:
        offset = 0
        next_auxiliary = 10_001
        allocated: set[int] = set()
        sections = (
            ("rows", all_rows(100), True, 100, 700, 70_100),
            ("columns", all_columns(100), True, 100, 700, 70_100),
            ("main diagonals", all_main_diagonals(100), False, 197, 1_139, 64_412),
            ("anti diagonals", all_anti_diagonals(100), False, 197, 1_139, 64_412),
        )
        for name, groups, exactly_one, group_count, expected_aux, expected_clauses in sections:
            section_start = offset
            section_aux_start = next_auxiliary
            self.assertEqual(len(groups), group_count)
            for group_index, group in enumerate(groups):
                with self.subTest(section=name, group=group_index):
                    if exactly_one:
                        self.assertEqual(self.cnf[offset], group)
                        offset += 1
                    m = len(group)
                    bits = (m - 1).bit_length()
                    expected_ids = set(range(next_auxiliary, next_auxiliary + bits))
                    original_ids = set(group)
                    self.assertTrue(all(1 <= var <= 10_000 for var in original_ids))
                    used_auxiliaries: set[int] = set()
                    original_counts: Counter[int] = Counter()
                    implications: set[tuple[int, int]] = set()
                    for _ in range(m * bits):
                        clause = self.cnf[offset]
                        self.assertEqual(len(clause), 2)
                        self.assertLess(clause[0], 0)
                        original = -clause[0]
                        auxiliary = abs(clause[1])
                        self.assertIn(original, original_ids)
                        self.assertIn(auxiliary, expected_ids)
                        original_counts[original] += 1
                        used_auxiliaries.add(auxiliary)
                        implications.add((original, auxiliary))
                        offset += 1
                    self.assertEqual(original_counts, Counter({var: bits for var in group}))
                    self.assertEqual(len(implications), m * bits)
                    self.assertEqual(used_auxiliaries, expected_ids)
                    self.assertTrue(allocated.isdisjoint(used_auxiliaries))
                    allocated.update(used_auxiliaries)
                    next_auxiliary += bits
            self.assertEqual(offset - section_start, expected_clauses, name)
            self.assertEqual(next_auxiliary - section_aux_start, expected_aux, name)

        self.assertEqual(offset, len(self.cnf))
        self.assertEqual(next_auxiliary, self.total_variables + 1)
        self.assertEqual(allocated, set(range(10_001, 13_679)))


if __name__ == "__main__":
    unittest.main()
