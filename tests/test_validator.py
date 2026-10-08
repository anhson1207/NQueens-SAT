"""Unit tests for solver-independent N-Queens solution validation."""

import unittest

from src.common.validator import validate_columns, validate_positions


class TestValidatePositions(unittest.TestCase):
    def test_valid_n4_solution(self) -> None:
        positions = [(0, 1), (1, 3), (2, 0), (3, 2)]
        self.assertTrue(validate_positions(positions, 4))

    def test_valid_solution_in_any_order(self) -> None:
        positions = [(2, 0), (0, 1), (3, 2), (1, 3)]
        self.assertTrue(validate_positions(positions, 4))

    def test_wrong_number_of_queens(self) -> None:
        for positions in (
            [],
            [(0, 1), (1, 3), (2, 0)],
            [(0, 1), (1, 3), (2, 0), (3, 2), (0, 0)],
        ):
            with self.subTest(positions=positions):
                self.assertFalse(validate_positions(positions, 4))

    def test_duplicate_row(self) -> None:
        for positions in (
            [(0, 0), (0, 2), (2, 1), (3, 3)],
            # Only a row conflict: columns and both diagonal sets are distinct.
            [(0, 1), (0, 3), (2, 0), (3, 2)],
        ):
            with self.subTest(positions=positions):
                self.assertFalse(validate_positions(positions, 4))

    def test_duplicate_column(self) -> None:
        for positions in (
            [(0, 1), (1, 1), (2, 3), (3, 0)],
            # Only a column conflict: rows and both diagonal sets are distinct.
            [(1, 0), (3, 0), (0, 2), (2, 3)],
        ):
            with self.subTest(positions=positions):
                self.assertFalse(validate_positions(positions, 4))

    def test_main_diagonal_conflict(self) -> None:
        positions = [(0, 0), (1, 1), (2, 2), (3, 3)]
        self.assertFalse(validate_positions(positions, 4))

    def test_anti_diagonal_conflict(self) -> None:
        positions = [(0, 3), (1, 2), (2, 1), (3, 0)]
        self.assertFalse(validate_positions(positions, 4))

    def test_queen_outside_board(self) -> None:
        for outside in (
            (-1, 1), (4, 1), (0, -1), (0, 4),
            (-5, 1), (7, 1), (0, -5), (0, 7),
        ):
            with self.subTest(position=outside):
                positions = [outside, (1, 3), (2, 0), (3, 2)]
                self.assertFalse(validate_positions(positions, 4))

    def test_single_queen(self) -> None:
        self.assertTrue(validate_positions([(0, 0)], 1))

    def test_invalid_board_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n):
                self.assertFalse(validate_positions([], n))


class TestValidateColumns(unittest.TestCase):
    def test_valid_columns(self) -> None:
        self.assertTrue(validate_columns([1, 3, 0, 2]))

    def test_invalid_columns(self) -> None:
        self.assertFalse(validate_columns([0, 1, 2, 3]))

    def test_duplicate_column(self) -> None:
        self.assertFalse(validate_columns([1, 1, 3, 0]))

    def test_column_outside_board(self) -> None:
        for columns in ([-1, 3, 0, 2], [4, 3, 0, 2]):
            with self.subTest(columns=columns):
                self.assertFalse(validate_columns(columns))

    def test_empty_columns(self) -> None:
        self.assertFalse(validate_columns([]))

    def test_single_queen(self) -> None:
        self.assertTrue(validate_columns([0]))


if __name__ == "__main__":
    unittest.main()
