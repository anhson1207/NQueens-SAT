"""Encode AMO with a non-recursive 2-Product auxiliary grid."""

from math import isqrt

from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.pairwise import (
    _validate_variables,
    encode_alo,
    encode_amo_pairwise,
)
from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_rows,
    first_auxiliary_variable,
)


def encode_amo_product(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    """Forbid two true originals using Pairwise AMO on a 2-Product grid."""
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    if not isinstance(allocator, AuxiliaryVariableAllocator):
        raise ValueError("allocator must be an AuxiliaryVariableAllocator")
    _validate_variables(variables, allow_empty=True)

    first_auxiliary_id = allocator.next_id - allocator.allocated_count
    if any(variable >= first_auxiliary_id for variable in variables):
        raise ValueError("Original IDs must be below the allocator's initial start_id")

    m = len(variables)
    if m <= 1:
        return []

    p = isqrt(m)
    if p * p < m:
        p += 1
    q = (m + p - 1) // p

    row_variables = [allocator.new_var() for _ in range(p)]
    column_variables = [allocator.new_var() for _ in range(q)]
    clauses: list[list[int]] = []
    for index, variable in enumerate(variables):
        clauses.append([-variable, row_variables[index // q]])
        clauses.append([-variable, column_variables[index % q]])
    clauses.extend(encode_amo_pairwise(row_variables))
    clauses.extend(encode_amo_pairwise(column_variables))
    return clauses


def encode_exactly_one_product(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    """Require exactly one true original with ALO followed by Product AMO."""
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    if not isinstance(allocator, AuxiliaryVariableAllocator):
        raise ValueError("allocator must be an AuxiliaryVariableAllocator")
    return encode_alo(variables) + encode_amo_product(variables, allocator)


def encode_nqueens_product(n: int) -> tuple[list[list[int]], int]:
    """Return N-Queens 2-Product CNF and its total reserved variable count."""
    allocator = AuxiliaryVariableAllocator(first_auxiliary_variable(n))
    clauses: list[list[int]] = []

    for row in all_rows(n):
        clauses.extend(encode_exactly_one_product(row, allocator))
    for column in all_columns(n):
        clauses.extend(encode_exactly_one_product(column, allocator))
    for diagonal in all_main_diagonals(n):
        clauses.extend(encode_amo_product(diagonal, allocator))
    for diagonal in all_anti_diagonals(n):
        clauses.extend(encode_amo_product(diagonal, allocator))

    return clauses, n * n + allocator.allocated_count
