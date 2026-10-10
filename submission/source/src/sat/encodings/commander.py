"""Encode AMO with recursive Commander groups and local Pairwise constraints."""

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


def _validate_group_size(group_size: int) -> None:
    """Require an integer group size that makes recursive groups shrink."""
    if (
        not isinstance(group_size, int)
        or isinstance(group_size, bool)
        or group_size < 2
    ):
        raise ValueError("group_size must be an integer >= 2")


def _encode_amo_recursive(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
    group_size: int,
) -> list[list[int]]:
    """Encode validated originals or internally allocated commanders recursively."""
    if len(variables) <= 1:
        return []
    if len(variables) <= group_size:
        return encode_amo_pairwise(variables)

    groups = [
        variables[start:start + group_size]
        for start in range(0, len(variables), group_size)
    ]
    commanders = [allocator.new_var() for _ in groups]
    clauses: list[list[int]] = []
    for group, commander in zip(groups, commanders):
        clauses.extend(encode_amo_pairwise(group))
        clauses.extend([[-variable, commander] for variable in group])
    clauses.extend(_encode_amo_recursive(commanders, allocator, group_size))
    return clauses


def encode_amo_commander(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
    group_size: int = 3,
) -> list[list[int]]:
    """Forbid two true originals using fresh recursive Commander variables."""
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    if not isinstance(allocator, AuxiliaryVariableAllocator):
        raise ValueError("allocator must be an AuxiliaryVariableAllocator")
    _validate_group_size(group_size)
    _validate_variables(variables, allow_empty=True)

    first_auxiliary_id = allocator.next_id - allocator.allocated_count
    if any(variable >= first_auxiliary_id for variable in variables):
        raise ValueError("Original IDs must be below the allocator's initial start_id")
    return _encode_amo_recursive(variables, allocator, group_size)


def encode_exactly_one_commander(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
    group_size: int = 3,
) -> list[list[int]]:
    """Require exactly one true original with ALO followed by Commander AMO."""
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    if not isinstance(allocator, AuxiliaryVariableAllocator):
        raise ValueError("allocator must be an AuxiliaryVariableAllocator")
    _validate_group_size(group_size)
    return encode_alo(variables) + encode_amo_commander(
        variables, allocator, group_size
    )


def encode_nqueens_commander(
    n: int,
    group_size: int = 3,
) -> tuple[list[list[int]], int]:
    """Return N-Queens Commander CNF and its total reserved variable count."""
    _validate_group_size(group_size)
    allocator = AuxiliaryVariableAllocator(first_auxiliary_variable(n))
    clauses: list[list[int]] = []

    for row in all_rows(n):
        clauses.extend(encode_exactly_one_commander(row, allocator, group_size))
    for column in all_columns(n):
        clauses.extend(encode_exactly_one_commander(column, allocator, group_size))
    for diagonal in all_main_diagonals(n):
        clauses.extend(encode_amo_commander(diagonal, allocator, group_size))
    for diagonal in all_anti_diagonals(n):
        clauses.extend(encode_amo_commander(diagonal, allocator, group_size))

    return clauses, n * n + allocator.allocated_count
