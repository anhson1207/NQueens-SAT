"""Check SAT ID mapping and variable groups for all 10,000 cells at N=100."""

import unittest

from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_rows,
    first_auxiliary_variable,
    position_from_var,
    primary_variable_count,
    var_id,
)


class TestN100SATModel(unittest.TestCase):
    n = 100

    def test_variable_count(self) -> None:
        self.assertEqual(primary_variable_count(self.n), 10000)
        self.assertEqual(first_auxiliary_variable(self.n), 10001)

    def test_variable_mapping_is_unique(self) -> None:
        variable_ids = [
            var_id(row, col, self.n)
            for row in range(self.n)
            for col in range(self.n)
        ]
        self.assertEqual(len(variable_ids), 10000)
        self.assertEqual(len(set(variable_ids)), 10000)
        self.assertEqual(min(variable_ids), 1)
        self.assertEqual(max(variable_ids), 10000)

    def test_mapping_round_trip(self) -> None:
        for row in range(self.n):
            for col in range(self.n):
                with self.subTest(row=row, col=col):
                    self.assertEqual(
                        position_from_var(var_id(row, col, self.n), self.n),
                        (row, col),
                    )

    def test_row_groups(self) -> None:
        rows = all_rows(self.n)
        self.assertEqual(len(rows), 100)
        self.assertTrue(all(len(group) == 100 for group in rows))
        flattened = [variable for group in rows for variable in group]
        self.assertEqual(len(flattened), 10000)
        self.assertEqual(len(set(flattened)), 10000)
        self.assertEqual(set(flattened), set(range(1, 10001)))

    def test_column_groups(self) -> None:
        columns = all_columns(self.n)
        self.assertEqual(len(columns), 100)
        self.assertTrue(all(len(group) == 100 for group in columns))
        flattened = [variable for group in columns for variable in group]
        self.assertEqual(len(flattened), 10000)
        self.assertEqual(len(set(flattened)), 10000)
        self.assertEqual(set(flattened), set(range(1, 10001)))

    def test_main_diagonals(self) -> None:
        diagonals = all_main_diagonals(self.n)
        self.assertEqual(len(diagonals), 197)
        self.assertTrue(all(len(group) >= 2 for group in diagonals))
        self.assertEqual(max(len(group) for group in diagonals), 100)
        self.assertIn([var_id(i, i, self.n) for i in range(self.n)], diagonals)

    def test_anti_diagonals(self) -> None:
        diagonals = all_anti_diagonals(self.n)
        self.assertEqual(len(diagonals), 197)
        self.assertTrue(all(len(group) >= 2 for group in diagonals))
        self.assertEqual(max(len(group) for group in diagonals), 100)
        self.assertIn([var_id(i, 99 - i, self.n) for i in range(self.n)], diagonals)

    def test_diagonals_partition_all_variables(self) -> None:
        for get_groups in (all_main_diagonals, all_anti_diagonals):
            with self.subTest(group=get_groups.__name__):
                groups = get_groups(self.n, min_length=1)
                self.assertEqual(len(groups), 199)
                flattened = [variable for group in groups for variable in group]
                self.assertEqual(len(flattened), 10000)
                self.assertEqual(len(set(flattened)), 10000)
                self.assertEqual(set(flattened), set(range(1, 10001)))

    def test_diagonal_groups_are_deterministic(self) -> None:
        for get_groups in (all_main_diagonals, all_anti_diagonals):
            with self.subTest(group=get_groups.__name__):
                self.assertEqual(get_groups(self.n), get_groups(self.n))


if __name__ == "__main__":
    unittest.main()
