"""Unit tests for SAT variable mapping and N-Queens domain groups."""

import unittest

from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_primary_variables,
    all_rows,
    column_variables,
    first_auxiliary_variable,
    position_from_var,
    primary_variable_count,
    row_variables,
    var_id,
)


class TestVariableMapping(unittest.TestCase):
    def test_var_id_n4(self) -> None:
        for row, col, expected in ((0, 0, 1), (0, 3, 4), (1, 0, 5), (3, 3, 16)):
            with self.subTest(row=row, col=col):
                self.assertEqual(var_id(row, col, 4), expected)

    def test_position_from_var_n4(self) -> None:
        for variable, expected in ((1, (0, 0)), (4, (0, 3)), (5, (1, 0)), (16, (3, 3))):
            with self.subTest(variable=variable):
                self.assertEqual(position_from_var(variable, 4), expected)

    def test_mapping_round_trip(self) -> None:
        for n in (1, 4, 8):
            for row in range(n):
                for col in range(n):
                    with self.subTest(n=n, row=row, col=col):
                        self.assertEqual(position_from_var(var_id(row, col, n), n), (row, col))

    def test_variable_ids_are_unique_and_cover_the_board(self) -> None:
        ids = [var_id(row, col, 8) for row in range(8) for col in range(8)]
        self.assertEqual(len(ids), 64)
        self.assertEqual(len(set(ids)), 64)
        self.assertEqual(min(ids), 1)
        self.assertEqual(max(ids), 64)

    def test_primary_variable_count(self) -> None:
        for n, expected in ((1, 1), (4, 16), (8, 64), (100, 10000)):
            with self.subTest(n=n):
                self.assertEqual(primary_variable_count(n), expected)

    def test_first_auxiliary_variable(self) -> None:
        for n, expected in ((1, 2), (4, 17), (8, 65), (100, 10001)):
            with self.subTest(n=n):
                self.assertEqual(first_auxiliary_variable(n), expected)

    def test_all_primary_variables(self) -> None:
        self.assertEqual(all_primary_variables(4), list(range(1, 17)))
        self.assertEqual(all_primary_variables(8), list(range(1, 65)))

    def test_var_id_rejects_out_of_bounds_positions(self) -> None:
        for row, col in ((-1, 0), (4, 0), (0, -1), (0, 4)):
            with self.subTest(row=row, col=col):
                with self.assertRaises(ValueError):
                    var_id(row, col, 4)

    def test_position_from_var_rejects_non_primary_ids(self) -> None:
        for variable in (-1, 0, 17, 100):
            with self.subTest(variable=variable):
                with self.assertRaises(ValueError):
                    position_from_var(variable, 4)


class TestRowAndColumnGroups(unittest.TestCase):
    def test_row_variables(self) -> None:
        for row, expected in ((0, [1, 2, 3, 4]), (1, [5, 6, 7, 8]), (3, [13, 14, 15, 16])):
            with self.subTest(row=row):
                self.assertEqual(row_variables(row, 4), expected)

    def test_column_variables(self) -> None:
        for col, expected in ((0, [1, 5, 9, 13]), (1, [2, 6, 10, 14]), (3, [4, 8, 12, 16])):
            with self.subTest(col=col):
                self.assertEqual(column_variables(col, 4), expected)

    def test_all_rows_n4(self) -> None:
        self.assertEqual(
            all_rows(4),
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
        )

    def test_all_columns_n4(self) -> None:
        self.assertEqual(
            all_columns(4),
            [[1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15], [4, 8, 12, 16]],
        )

    def test_rows_and_columns_partition_all_primary_variables(self) -> None:
        for n in (1, 2, 4, 8):
            for get_groups in (all_rows, all_columns):
                with self.subTest(n=n, group=get_groups.__name__):
                    groups = get_groups(n)
                    self.assertEqual(len(groups), n)
                    self.assertTrue(all(len(group) == n for group in groups))
                    flattened = [variable for group in groups for variable in group]
                    self.assertEqual(sorted(flattened), list(range(1, n * n + 1)))

    def test_invalid_row(self) -> None:
        for row in (-1, 4):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    row_variables(row, 4)

    def test_invalid_column(self) -> None:
        for col in (-1, 4):
            with self.subTest(col=col):
                with self.assertRaises(ValueError):
                    column_variables(col, 4)


class TestDiagonalGroups(unittest.TestCase):
    def test_main_diagonals_n4(self) -> None:
        self.assertEqual(
            all_main_diagonals(4),
            [[3, 8], [2, 7, 12], [1, 6, 11, 16], [5, 10, 15], [9, 14]],
        )

    def test_anti_diagonals_n4(self) -> None:
        self.assertEqual(
            all_anti_diagonals(4),
            [[2, 5], [3, 6, 9], [4, 7, 10, 13], [8, 11, 14], [12, 15]],
        )

    def test_default_diagonal_lengths_n4(self) -> None:
        for get_groups in (all_main_diagonals, all_anti_diagonals):
            with self.subTest(group=get_groups.__name__):
                groups = get_groups(4)
                self.assertEqual(len(groups), 5)
                self.assertEqual([len(group) for group in groups], [2, 3, 4, 3, 2])

    def test_main_diagonals_including_singletons(self) -> None:
        self.assertEqual(
            all_main_diagonals(4, min_length=1),
            [[4], [3, 8], [2, 7, 12], [1, 6, 11, 16], [5, 10, 15], [9, 14], [13]],
        )

    def test_anti_diagonals_including_singletons(self) -> None:
        self.assertEqual(
            all_anti_diagonals(4, min_length=1),
            [[1], [2, 5], [3, 6, 9], [4, 7, 10, 13], [8, 11, 14], [12, 15], [16]],
        )

    def test_diagonal_keys_order_and_cell_coverage(self) -> None:
        for n in (1, 2, 4, 8):
            for get_groups in (all_main_diagonals, all_anti_diagonals):
                with self.subTest(n=n, group=get_groups.__name__):
                    groups = get_groups(n, min_length=1)
                    self.assertEqual(len(groups), 2 * n - 1)
                    flattened = [variable for group in groups for variable in group]
                    self.assertEqual(sorted(flattened), list(range(1, n * n + 1)))
                    keys = []
                    for group in groups:
                        positions = [position_from_var(variable, n) for variable in group]
                        rows = [row for row, _ in positions]
                        self.assertEqual(rows, sorted(rows))
                        if get_groups is all_main_diagonals:
                            group_keys = {row - col for row, col in positions}
                        else:
                            group_keys = {row + col for row, col in positions}
                        self.assertEqual(len(group_keys), 1)
                        keys.append(next(iter(group_keys)))
                    expected_keys = (
                        list(range(-(n - 1), n))
                        if get_groups is all_main_diagonals
                        else list(range(2 * n - 1))
                    )
                    self.assertEqual(keys, expected_keys)

    def test_custom_minimum_length(self) -> None:
        self.assertEqual(
            all_main_diagonals(4, min_length=3),
            [[2, 7, 12], [1, 6, 11, 16], [5, 10, 15]],
        )
        self.assertEqual(
            all_anti_diagonals(4, min_length=3),
            [[3, 6, 9], [4, 7, 10, 13], [8, 11, 14]],
        )
        self.assertEqual(all_main_diagonals(4, min_length=4), [[1, 6, 11, 16]])
        self.assertEqual(all_anti_diagonals(4, min_length=4), [[4, 7, 10, 13]])

    def test_minimum_length_larger_than_board(self) -> None:
        for get_groups in (all_main_diagonals, all_anti_diagonals):
            with self.subTest(group=get_groups.__name__):
                self.assertEqual(get_groups(4, min_length=5), [])

    def test_invalid_minimum_length(self) -> None:
        for get_groups in (all_main_diagonals, all_anti_diagonals):
            for min_length in (0, -1):
                with self.subTest(group=get_groups.__name__, min_length=min_length):
                    with self.assertRaises(ValueError):
                        get_groups(4, min_length=min_length)


class TestBoardSizes(unittest.TestCase):
    def test_single_cell_board(self) -> None:
        self.assertEqual(var_id(0, 0, 1), 1)
        self.assertEqual(position_from_var(1, 1), (0, 0))
        self.assertEqual(primary_variable_count(1), 1)
        self.assertEqual(first_auxiliary_variable(1), 2)
        self.assertEqual(all_primary_variables(1), [1])
        self.assertEqual(all_rows(1), [[1]])
        self.assertEqual(all_columns(1), [[1]])
        self.assertEqual(all_main_diagonals(1), [])
        self.assertEqual(all_anti_diagonals(1), [])
        self.assertEqual(all_main_diagonals(1, min_length=1), [[1]])
        self.assertEqual(all_anti_diagonals(1, min_length=1), [[1]])

    def test_all_public_functions_reject_invalid_board_sizes(self) -> None:
        for n in (0, -1):
            for function, args in (
                (var_id, (0, 0, n)),
                (position_from_var, (1, n)),
                (primary_variable_count, (n,)),
                (first_auxiliary_variable, (n,)),
                (row_variables, (0, n)),
                (column_variables, (0, n)),
                (all_rows, (n,)),
                (all_columns, (n,)),
                (all_main_diagonals, (n,)),
                (all_anti_diagonals, (n,)),
                (all_primary_variables, (n,)),
            ):
                with self.subTest(function=function.__name__, n=n):
                    with self.assertRaises(ValueError):
                        function(*args)


if __name__ == "__main__":
    unittest.main()
