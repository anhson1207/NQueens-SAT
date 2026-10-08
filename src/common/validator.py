"""Validate N-Queens solutions independently of any solver."""

from src.common.board import columns_to_positions


def validate_positions(positions: list[tuple[int, int]], n: int) -> bool:
    """Check bounds, queen count, and all conflicts in O(n) time and space."""
    if n < 1 or len(positions) != n:
        return False

    rows: set[int] = set()
    cols: set[int] = set()
    main_diagonals: set[int] = set()
    anti_diagonals: set[int] = set()

    for row, col in positions:
        if not (0 <= row < n and 0 <= col < n):
            return False

        main_diagonal = row - col
        anti_diagonal = row + col
        if (
            row in rows
            or col in cols
            or main_diagonal in main_diagonals
            or anti_diagonal in anti_diagonals
        ):
            return False

        rows.add(row)
        cols.add(col)
        main_diagonals.add(main_diagonal)
        anti_diagonals.add(anti_diagonal)

    return True


def validate_columns(columns: list[int]) -> bool:
    """Validate a solution given as one queen column per row."""
    return validate_positions(columns_to_positions(columns), len(columns))
