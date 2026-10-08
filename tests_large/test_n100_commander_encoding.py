"""Inspect one N=100 Commander CNF and every recursive private commander set."""

import unittest

from src.sat.encodings.commander import encode_nqueens_commander
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


def reference_amo_counts(m: int, group_size: int = 3) -> tuple[int, int]:
    """Count auxiliaries and clauses from the recursive specification."""
    if m <= 1:
        return 0, 0
    if m <= group_size:
        return 0, m * (m - 1) // 2
    sizes = [
        min(group_size, m - start)
        for start in range(0, m, group_size)
    ]
    child_aux, child_clauses = reference_amo_counts(len(sizes), group_size)
    return (
        len(sizes) + child_aux,
        m + sum(size * (size - 1) // 2 for size in sizes) + child_clauses,
    )


class TestN100CommanderEncoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cnf, cls.total_variables = encode_nqueens_commander(100)

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.cnf

    def test_counts(self) -> None:
        self.assertEqual(self.total_variables, 30_536)
        self.assertEqual(self.total_variables - 10_000, 20_536)
        self.assertEqual(len(self.cnf), 118_092)

    def test_literal_ranges_and_nonempty_clauses(self) -> None:
        self.assertTrue(all(self.cnf), "CNF contains an empty clause")
        self.assertTrue(all(
            isinstance(lit, int) and not isinstance(lit, bool) and 1 <= abs(lit) <= 30_536
            for clause in self.cnf for lit in clause
        ))
        used_ids = {abs(lit) for clause in self.cnf for lit in clause}
        self.assertEqual(used_ids, set(range(1, 30_537)))
        self.assertEqual(min(var for var in used_ids if var > 10_000), 10_001)

    def _check_group(
        self,
        variables: list[int],
        offset: int,
        next_auxiliary: int,
        allocated: set[int],
    ) -> tuple[int, int]:
        if len(variables) <= 1:
            return offset, next_auxiliary
        if len(variables) <= 3:
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    self.assertEqual(self.cnf[offset], [-variables[i], -variables[j]])
                    offset += 1
            return offset, next_auxiliary

        groups = [variables[start:start + 3] for start in range(0, len(variables), 3)]
        commanders = list(range(next_auxiliary, next_auxiliary + len(groups)))
        self.assertTrue(allocated.isdisjoint(commanders))
        allocated.update(commanders)
        next_auxiliary += len(groups)

        for group, commander in zip(groups, commanders):
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    self.assertEqual(self.cnf[offset], [-group[i], -group[j]])
                    offset += 1
            for variable in group:
                self.assertEqual(self.cnf[offset], [-variable, commander])
                offset += 1
        return self._check_group(commanders, offset, next_auxiliary, allocated)

    def test_every_group_has_expected_partition_recursion_and_clause_order(self) -> None:
        offset = 0
        next_auxiliary = 10_001
        allocated: set[int] = set()
        sections = (
            ("rows", all_rows(100), True),
            ("columns", all_columns(100), True),
            ("main diagonals", all_main_diagonals(100), False),
            ("anti diagonals", all_anti_diagonals(100), False),
        )
        expected_total_aux = 0
        expected_total_clauses = 0
        for name, groups, exactly_one in sections:
            section_start = offset
            section_aux_start = next_auxiliary
            reference_section_aux = 0
            reference_section_clauses = 0
            for group_index, group in enumerate(groups):
                with self.subTest(section=name, group=group_index):
                    group_aux, group_clauses = reference_amo_counts(len(group))
                    reference_section_aux += group_aux
                    reference_section_clauses += group_clauses + int(exactly_one)
                    if exactly_one:
                        self.assertEqual(self.cnf[offset], group)
                        offset += 1
                    offset, next_auxiliary = self._check_group(
                        group, offset, next_auxiliary, allocated
                    )
            self.assertEqual(next_auxiliary - section_aux_start, reference_section_aux)
            self.assertEqual(offset - section_start, reference_section_clauses)
            expected_total_aux += reference_section_aux
            expected_total_clauses += reference_section_clauses

        self.assertEqual(expected_total_aux, 20_536)
        self.assertEqual(expected_total_clauses, 118_092)
        self.assertEqual(offset, len(self.cnf))
        self.assertEqual(next_auxiliary, self.total_variables + 1)
        self.assertEqual(allocated, set(range(10_001, 30_537)))


if __name__ == "__main__":
    unittest.main()
