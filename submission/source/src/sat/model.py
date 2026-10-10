"""Map N-Queens cells to SAT IDs and group variables without creating clauses.

Rows and columns will require exactly-one constraints; diagonals will require
at-most-one constraints. Encoding and solving belong to separate modules.
"""


def _validate_n(n: int) -> None:
    """Reject non-positive board sizes."""
    if n < 1:
        raise ValueError("n must be at least 1")


def var_id(row: int, col: int, n: int) -> int:
    """Map a zero-based board position to a one-based primary variable ID."""
    _validate_n(n)
    if not (0 <= row < n and 0 <= col < n):
        raise ValueError(f"Position {(row, col)} is outside a {n}x{n} board")
    return row * n + col + 1


def position_from_var(variable: int, n: int) -> tuple[int, int]:
    """Decode a primary variable ID; reject auxiliary IDs and signed literals."""
    if not 1 <= variable <= primary_variable_count(n):
        raise ValueError(f"Variable must be between 1 and {n * n}")
    return divmod(variable - 1, n)


def primary_variable_count(n: int) -> int:
    """Return the number of primary variables for an n-by-n board."""
    _validate_n(n)
    return n * n


def first_auxiliary_variable(n: int) -> int:
    """Return the first available auxiliary ID without allocating any variables."""
    return primary_variable_count(n) + 1


def row_variables(row: int, n: int) -> list[int]:
    """Return one row's primary IDs in increasing column order."""
    _validate_n(n)
    if not 0 <= row < n:
        raise ValueError(f"Row must be between 0 and {n - 1}")
    return [var_id(row, col, n) for col in range(n)]


def column_variables(col: int, n: int) -> list[int]:
    """Return one column's primary IDs in increasing row order."""
    _validate_n(n)
    if not 0 <= col < n:
        raise ValueError(f"Column must be between 0 and {n - 1}")
    return [var_id(row, col, n) for row in range(n)]


def all_rows(n: int) -> list[list[int]]:
    """Return row groups from top to bottom."""
    _validate_n(n)
    return [row_variables(row, n) for row in range(n)]


def all_columns(n: int) -> list[list[int]]:
    """Return column groups from left to right."""
    _validate_n(n)
    return [column_variables(col, n) for col in range(n)]


def all_main_diagonals(n: int, min_length: int = 2) -> list[list[int]]:
    """Group IDs by increasing row-col, with cells ordered top to bottom."""
    _validate_n(n)
    if min_length < 1:
        raise ValueError("min_length must be at least 1")
    if min_length > n:
        return []

    diagonals: dict[int, list[int]] = {}
    for row in range(n):
        for col in range(n):
            diagonals.setdefault(row - col, []).append(var_id(row, col, n))

    return [
        diagonals[key]
        for key in range(-(n - 1), n)
        if len(diagonals[key]) >= min_length
    ]


def all_anti_diagonals(n: int, min_length: int = 2) -> list[list[int]]:
    """Group IDs by increasing row+col, with cells ordered top to bottom."""
    _validate_n(n)
    if min_length < 1:
        raise ValueError("min_length must be at least 1")
    if min_length > n:
        return []

    diagonals: dict[int, list[int]] = {}
    for row in range(n):
        for col in range(n):
            diagonals.setdefault(row + col, []).append(var_id(row, col, n))

    return [
        diagonals[key]
        for key in range(2 * n - 1)
        if len(diagonals[key]) >= min_length
    ]


def all_primary_variables(n: int) -> list[int]:
    """Return all primary variable IDs in increasing order."""
    return list(range(1, primary_variable_count(n) + 1))
