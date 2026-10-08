"""Inspect one N=100 Sequential CNF and every group's private counter chain."""

import unittest

from src.sat.encodings.sequential import encode_nqueens_sequential
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


class TestN100SequentialEncoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cnf, cls.total_variables = encode_nqueens_sequential(100)

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.cnf

    def test_counts(self) -> None:
        self.assertEqual(self.total_variables, 49_402)
        self.assertEqual(self.total_variables - 10_000, 39_402)
        self.assertEqual(len(self.cnf), 117_812)

    def test_literal_ranges_and_nonempty_clauses(self) -> None:
        self.assertTrue(all(self.cnf), "CNF contains an empty clause")
        self.assertTrue(all(
            isinstance(lit, int) and not isinstance(lit, bool) and 1 <= abs(lit) <= 49_402
            for clause in self.cnf for lit in clause
        ))
        used_ids = {abs(lit) for clause in self.cnf for lit in clause}
        self.assertEqual(used_ids, set(range(1, 49_403)))
        self.assertEqual(min(var for var in used_ids if var > 10_000), 10_001)

    def test_every_group_has_expected_private_chain_and_clause_order(self) -> None:
        offset = 0
        next_auxiliary = 10_001
        allocated: set[int] = set()
        sections = (
            ("rows", all_rows(100), True, 100, 9_900, 29_700),
            ("columns", all_columns(100), True, 100, 9_900, 29_700),
            ("main diagonals", all_main_diagonals(100), False, 197, 9_801, 29_206),
            ("anti diagonals", all_anti_diagonals(100), False, 197, 9_801, 29_206),
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
                    counters = list(range(next_auxiliary, next_auxiliary + m - 1))
                    self.assertTrue(allocated.isdisjoint(counters))
                    self.assertEqual(self.cnf[offset], [-group[0], counters[0]])
                    offset += 1
                    for index in range(1, m - 1):
                        expected = (
                            [-group[index], counters[index]],
                            [-counters[index - 1], counters[index]],
                            [-group[index], -counters[index - 1]],
                        )
                        for clause in expected:
                            self.assertEqual(self.cnf[offset], clause)
                            offset += 1
                    self.assertEqual(self.cnf[offset], [-group[-1], -counters[-1]])
                    offset += 1
                    allocated.update(counters)
                    next_auxiliary += m - 1

            self.assertEqual(offset - section_start, expected_clauses, name)
            self.assertEqual(next_auxiliary - section_aux_start, expected_aux, name)

        self.assertEqual(offset, len(self.cnf))
        self.assertEqual(next_auxiliary, self.total_variables + 1)
        self.assertEqual(allocated, set(range(10_001, 49_403)))


if __name__ == "__main__":
    unittest.main()
