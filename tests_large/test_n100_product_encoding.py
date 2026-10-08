"""Inspect one N=100 2-Product CNF and every group's private auxiliary grid."""

from math import isqrt
import unittest

from src.sat.encodings.product import encode_nqueens_product
from src.sat.model import all_anti_diagonals, all_columns, all_main_diagonals, all_rows


def reference_product_counts(m: int) -> tuple[int, int]:
    """Count auxiliaries and clauses from the fixed 2-Product specification."""
    if m <= 1:
        return 0, 0
    floor_root = isqrt(m)
    p = floor_root if floor_root * floor_root == m else floor_root + 1
    q = (m + p - 1) // p
    return p + q, 2 * m + p * (p - 1) // 2 + q * (q - 1) // 2


class TestN100ProductEncoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cnf, cls.total_variables = encode_nqueens_product(100)

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.cnf

    def test_counts(self) -> None:
        self.assertEqual(self.total_variables, 19_492)
        self.assertEqual(self.total_variables - 10_000, 9_492)
        self.assertEqual(len(self.cnf), 116_672)

    def test_literal_ranges_and_nonempty_clauses(self) -> None:
        self.assertTrue(all(self.cnf), "CNF contains an empty clause")
        self.assertTrue(all(
            isinstance(lit, int) and not isinstance(lit, bool) and 1 <= abs(lit) <= 19_492
            for clause in self.cnf for lit in clause
        ))
        used_ids = {abs(lit) for clause in self.cnf for lit in clause}
        self.assertEqual(used_ids, set(range(1, 19_493)))
        self.assertEqual(min(var for var in used_ids if var > 10_000), 10_001)

    def _check_group(
        self,
        variables: list[int],
        offset: int,
        next_auxiliary: int,
        allocated: set[int],
    ) -> tuple[int, int]:
        m = len(variables)
        if m <= 1:
            return offset, next_auxiliary

        floor_root = isqrt(m)
        p = floor_root if floor_root * floor_root == m else floor_root + 1
        q = (m + p - 1) // p
        rows = list(range(next_auxiliary, next_auxiliary + p))
        columns = list(range(next_auxiliary + p, next_auxiliary + p + q))
        auxiliaries = rows + columns
        self.assertTrue(allocated.isdisjoint(auxiliaries))
        allocated.update(auxiliaries)
        next_auxiliary += p + q

        for index, variable in enumerate(variables):
            self.assertEqual(self.cnf[offset], [-variable, rows[index // q]])
            offset += 1
            self.assertEqual(self.cnf[offset], [-variable, columns[index % q]])
            offset += 1
        for group in (rows, columns):
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    self.assertEqual(self.cnf[offset], [-group[i], -group[j]])
                    offset += 1
        return offset, next_auxiliary

    def test_every_group_has_expected_grid_mapping_and_clause_order(self) -> None:
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
                    group_aux, group_clauses = reference_product_counts(len(group))
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

        self.assertEqual(expected_total_aux, 9_492)
        self.assertEqual(expected_total_clauses, 116_672)
        self.assertEqual(offset, len(self.cnf))
        self.assertEqual(next_auxiliary, self.total_variables + 1)
        self.assertEqual(allocated, set(range(10_001, 19_493)))


if __name__ == "__main__":
    unittest.main()
