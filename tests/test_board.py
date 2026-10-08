"""Unit tests for N-Queens board conversion and display."""

from contextlib import redirect_stdout
from io import StringIO
import unittest

from src.common.board import (
    board_to_string,
    columns_to_positions,
    positions_to_board,
    print_board,
)


class TestBoard(unittest.TestCase):
    def test_positions_to_board(self) -> None:
        positions = [(0, 1), (1, 3), (2, 0), (3, 2)]
        expected = [
            [".", "Q", ".", "."],
            [".", ".", ".", "Q"],
            ["Q", ".", ".", "."],
            [".", ".", "Q", "."],
        ]
        self.assertEqual(positions_to_board(positions, 4), expected)

    def test_single_queen_board(self) -> None:
        self.assertEqual(positions_to_board([(0, 0)], 1), [["Q"]])

    def test_invalid_board_size(self) -> None:
        for n in (0, -1):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    positions_to_board([], n)

    def test_position_outside_board(self) -> None:
        for position in ((-1, 0), (4, 0), (0, -1), (0, 4)):
            with self.subTest(position=position):
                with self.assertRaises(ValueError):
                    positions_to_board([position], 4)

    def test_conversion_allows_partial_and_attacking_positions(self) -> None:
        board = positions_to_board([(0, 0), (0, 1)], 2)
        self.assertEqual(board, [["Q", "Q"], [".", "."]])

    def test_empty_board_has_independent_rows(self) -> None:
        board = positions_to_board([], 2)
        self.assertEqual(board, [[".", "."], [".", "."]])
        board[0][0] = "Q"
        self.assertEqual(board[1], [".", "."])

    def test_board_to_string(self) -> None:
        board = [
            [".", "Q", ".", "."],
            [".", ".", ".", "Q"],
            ["Q", ".", ".", "."],
            [".", ".", "Q", "."],
        ]
        output = StringIO()
        with redirect_stdout(output):
            text = board_to_string(board)
        self.assertEqual(text, ". Q . .\n. . . Q\nQ . . .\n. . Q .")
        self.assertEqual(output.getvalue(), "")

    def test_empty_board_to_string(self) -> None:
        self.assertEqual(board_to_string([]), "")

    def test_print_board(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = print_board([[".", "Q"], ["Q", "."]])
        self.assertIsNone(result)
        self.assertEqual(output.getvalue(), ". Q\nQ .\n")

    def test_columns_to_positions(self) -> None:
        self.assertEqual(
            columns_to_positions([1, 3, 0, 2]),
            [(0, 1), (1, 3), (2, 0), (3, 2)],
        )

    def test_empty_columns_to_positions(self) -> None:
        self.assertEqual(columns_to_positions([]), [])


if __name__ == "__main__":
    unittest.main()
