

def _validate_n(n: int) -> None:
    if n < 1:
        raise ValueError("n must be at least 1")


def var_id(row: int, col: int, n: int) -> int:
    _validate_n(n)
    if not (0 <= row < n and 0 <= col < n):
        raise ValueError(f"Position {(row, col)} is outside a {n}x{n} board")
    return row * n + col + 1


def position_from_var(variable: int, n: int) -> tuple[int, int]:
    if not 1 <= variable <= primary_variable_count(n):
        raise ValueError(f"Variable must be between 1 and {n * n}")
    return divmod(variable - 1, n)


def primary_variable_count(n: int) -> int:
    _validate_n(n)
    return n * n


def first_auxiliary_variable(n: int) -> int:
    return primary_variable_count(n) + 1


def row_variables(row: int, n: int) -> list[int]:
    _validate_n(n)
    if not 0 <= row < n:
        raise ValueError(f"Row must be between 0 and {n - 1}")
    return [var_id(row, col, n) for col in range(n)]


def column_variables(col: int, n: int) -> list[int]:
    _validate_n(n)
    if not 0 <= col < n:
        raise ValueError(f"Column must be between 0 and {n - 1}")
    return [var_id(row, col, n) for row in range(n)]


def all_rows(n: int) -> list[list[int]]:
    _validate_n(n)
    return [row_variables(row, n) for row in range(n)]


def all_columns(n: int) -> list[list[int]]:
    _validate_n(n)
    return [column_variables(col, n) for col in range(n)]


def all_main_diagonals(n: int, min_length: int = 2) -> list[list[int]]:
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
    return list(range(1, primary_variable_count(n) + 1))
