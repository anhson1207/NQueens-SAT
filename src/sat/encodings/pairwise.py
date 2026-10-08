"""Build Pairwise/Binomial N-Queens CNF without auxiliary variables or a solver."""

from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_rows,
)


def _validate_variables(variables: list[int], allow_empty: bool) -> None:
    """Require distinct positive integer IDs and the specified empty-list policy."""
    if not variables and not allow_empty:
        raise ValueError("variables must not be empty")

    seen: set[int] = set()
    for variable in variables:
        if (
            not isinstance(variable, int)
            or isinstance(variable, bool)
            or variable <= 0
        ):
            raise ValueError("Variable IDs must be positive integers")
        if variable in seen:
            raise ValueError(f"Duplicate variable ID: {variable}")
        seen.add(variable)


def encode_alo(variables: list[int]) -> list[list[int]]:
    """Require at least one variable to be true using one positive clause."""
    _validate_variables(variables, allow_empty=False)
    return [variables.copy()]


def encode_amo_pairwise(variables: list[int]) -> list[list[int]]:
    """Forbid every pair of true variables; empty and singleton groups need no clauses."""
    _validate_variables(variables, allow_empty=True)
    clauses: list[list[int]] = []
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            clauses.append([-variables[i], -variables[j]])
    return clauses


def encode_exactly_one_pairwise(variables: list[int]) -> list[list[int]]:
    """Require exactly one true variable by placing ALO before Pairwise AMO."""
    return encode_alo(variables) + encode_amo_pairwise(variables)


def encode_nqueens_pairwise(n: int) -> list[list[int]]:
    """Encode rows, columns, main diagonals, then anti diagonals without deduplication."""
    clauses: list[list[int]] = []

    for row in all_rows(n):
        clauses.extend(encode_exactly_one_pairwise(row))
    for column in all_columns(n):
        clauses.extend(encode_exactly_one_pairwise(column))
    for diagonal in all_main_diagonals(n):
        clauses.extend(encode_amo_pairwise(diagonal))
    for diagonal in all_anti_diagonals(n):
        clauses.extend(encode_amo_pairwise(diagonal))

    return clauses
