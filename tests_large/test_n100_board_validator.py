"""Check board conversion and independent validation on a 100-by-100 board."""

import unittest

from src.common.board import (
    board_to_string,
    columns_to_positions,
    positions_to_board,
)
from src.common.validator import validate_columns, validate_positions


class TestN100BoardValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.n = 100
        self.columns = list(range(1, self.n, 2)) + list(range(0, self.n, 2))
        self.positions = columns_to_positions(self.columns)

    def test_valid_solution(self) -> None:
        self.assertEqual(len(self.columns), 100)
        self.assertEqual(len(set(self.columns)), 100)
        self.assertIs(validate_columns(self.columns), True)
        self.assertEqual(len(self.positions), 100)
        self.assertIs(validate_positions(self.positions, self.n), True)
        self.assertTrue(
            all(0 <= row < self.n and 0 <= col < self.n for row, col in self.positions)
        )

    def test_board_representation(self) -> None:
        board = positions_to_board(self.positions, self.n)
        self.assertEqual(len(board), 100)
        self.assertTrue(all(len(row) == 100 for row in board))
        self.assertEqual(sum(row.count("Q") for row in board), 100)
        self.assertEqual(sum(row.count(".") for row in board), 9900)
        self.assertTrue(all(row.count("Q") == 1 for row in board))
        for col in range(self.n):
            with self.subTest(col=col):
                self.assertEqual(sum(board[row][col] == "Q" for row in range(self.n)), 1)
        for row, col in self.positions:
            self.assertEqual(board[row][col], "Q")

    def test_board_string(self) -> None:
        board = positions_to_board(self.positions, self.n)
        lines = board_to_string(board).splitlines()
        self.assertEqual(len(lines), 100)
        for row, line in enumerate(lines):
            with self.subTest(row=row):
                cells = line.split()
                self.assertEqual(len(cells), 100)
                self.assertEqual(cells, board[row])

    def test_duplicate_column(self) -> None:
        invalid = self.columns.copy()
        invalid[1] = invalid[0]
        self.assertIs(validate_columns(invalid), False)

    def test_main_diagonal_conflict(self) -> None:
        self.assertIs(validate_columns(list(range(self.n))), False)

    def test_anti_diagonal_conflict(self) -> None:
        self.assertIs(validate_columns(list(reversed(range(self.n)))), False)

    def test_queen_outside_board(self) -> None:
        invalid_positions = self.positions.copy()
        invalid_positions[0] = (100, 1)
        self.assertIs(validate_positions(invalid_positions, self.n), False)

    def test_wrong_number_of_queens(self) -> None:
        self.assertIs(validate_positions(self.positions[:-1], self.n), False)


if __name__ == "__main__":
    unittest.main()
