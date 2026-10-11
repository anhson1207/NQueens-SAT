
from src.sat.encodings.aux_vars import AuxiliaryVariableAllocator
from src.sat.encodings.pairwise import _validate_variables, encode_alo
from src.sat.model import (
    all_anti_diagonals,
    all_columns,
    all_main_diagonals,
    all_rows,
    first_auxiliary_variable,
)


def encode_amo_binary(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    _validate_variables(variables, allow_empty=True)
    first_auxiliary_id = allocator.next_id - allocator.allocated_count
    if any(variable >= first_auxiliary_id for variable in variables):
        raise ValueError("Original IDs must be below the allocator's initial start_id")

    m = len(variables)
    if m <= 1:
        return []

    bits = [allocator.new_var() for _ in range((m - 1).bit_length())]
    clauses: list[list[int]] = []
    for index, variable in enumerate(variables):
        for bit_index, auxiliary in enumerate(bits):
            bit_value = (index >> bit_index) & 1
            clauses.append([-variable, auxiliary if bit_value else -auxiliary])
    return clauses


def encode_exactly_one_binary(
    variables: list[int],
    allocator: AuxiliaryVariableAllocator,
) -> list[list[int]]:
    if not isinstance(variables, list):
        raise ValueError("variables must be a list of positive integer IDs")
    return encode_alo(variables) + encode_amo_binary(variables, allocator)


def encode_nqueens_binary(n: int) -> tuple[list[list[int]], int]:
    allocator = AuxiliaryVariableAllocator(first_auxiliary_variable(n))
    clauses: list[list[int]] = []

    for row in all_rows(n):
        clauses.extend(encode_exactly_one_binary(row, allocator))
    for column in all_columns(n):
        clauses.extend(encode_exactly_one_binary(column, allocator))
    for diagonal in all_main_diagonals(n):
        clauses.extend(encode_amo_binary(diagonal, allocator))
    for diagonal in all_anti_diagonals(n):
        clauses.extend(encode_amo_binary(diagonal, allocator))

    return clauses, n * n + allocator.allocated_count
