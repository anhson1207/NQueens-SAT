"""Encode AMO with the linear Sinz Sequential Counter formulation."""

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.pairwise import _validate_variables, encode_alo
from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_rows,
    first_auxiliary_variable,
)


def encode_amo_sequential(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    """Forbid two true originals with a fresh chain of m-1 variables.

    All original IDs must be below the allocator's initial start ID. For m >= 2,
    this exact Sinz variant creates m-1 auxiliaries and 3m-4 clauses.
    """
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    _validate_variables(variables, allow_empty=True)
    first_auxiliary_id = allocator.next_id - allocator.allocated_count
    if any(variable >= first_auxiliary_id for variable in variables):
        raise ValueError("Original IDs must be below the allocator's initial start_id")

    m = len(variables)
    if m <= 1:
        return []

    counters = [allocator.new_var() for _ in range(m - 1)]
    clauses: list[list[int]] = [[-variables[0], counters[0]]]
    for index in range(1, m - 1):
        variable = variables[index]
        previous = counters[index - 1]
        current = counters[index]
        clauses.extend(
            [
                [-variable, current],
                [-previous, current],
                [-variable, -previous],
            ]
        )
    clauses.append([-variables[-1], -counters[-1]])
    return clauses


def encode_exactly_one_sequential(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    """Require exactly one true original with ALO followed by Sequential AMO."""
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    return encode_alo(variables) + encode_amo_sequential(variables, allocator)


def encode_nqueens_sequential(n: int) -> tuple[list[list[int]], int]:
    """Return N-Queens Sequential CNF and its total reserved variable count."""
    allocator = AuxiliaryVariableAllocator(first_auxiliary_variable(n))
    clauses: list[list[int]] = []

    for row in all_rows(n):
        clauses.extend(encode_exactly_one_sequential(row, allocator))
    for column in all_columns(n):
        clauses.extend(encode_exactly_one_sequential(column, allocator))
    for diagonal in all_main_diagonals(n):
        clauses.extend(encode_amo_sequential(diagonal, allocator))
    for diagonal in all_anti_diagonals(n):
        clauses.extend(encode_amo_sequential(diagonal, allocator))

    return clauses, n * n + allocator.allocated_count
