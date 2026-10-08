"""Solve N-Queens CNF with Glucose3 and validate decoded primary variables."""

import argparse
import json
from random import Random
import sys
from time import perf_counter
from typing import Any

from pysat.solvers import Glucose3

from src.common.board import positions_to_board, print_board
from src.common.validator import validate_positions
from src.sat.encodings.binary import encode_nqueens_binary
from src.sat.encodings.commander import encode_nqueens_commander
from src.sat.encodings.pairwise import encode_nqueens_pairwise
from src.sat.encodings.product import encode_nqueens_product
from src.sat.encodings.sequential import encode_nqueens_sequential
from src.sat.model import position_from_var, primary_variable_count


PHASE_POLICIES = ("solver_default", "aux_false", "legacy")
LEGACY_PHASE_STRATEGIES = ("solver_default", "deterministic_aux_pattern")


def _validate_phase_configuration(
    phase_policy: str,
    legacy_phase_strategy: str,
) -> None:
    if phase_policy not in PHASE_POLICIES:
        raise ValueError(f"phase_policy must be one of: {', '.join(PHASE_POLICIES)}")
    if legacy_phase_strategy not in LEGACY_PHASE_STRATEGIES:
        raise ValueError(
            "legacy_phase_strategy must be one of: "
            + ", ".join(LEGACY_PHASE_STRATEGIES)
        )


def _phase_configuration(
    primary_variables: int,
    total_variables: int,
    phase_policy: str,
    legacy_phase_strategy: str,
) -> tuple[list[int], str]:
    """Build phase preferences without adding assumptions or CNF clauses."""
    auxiliary_ids = range(primary_variables + 1, total_variables + 1)
    if phase_policy == "solver_default":
        return [], "solver_default"
    if phase_policy == "aux_false":
        phases = [-variable for variable in auxiliary_ids]
        return phases, "aux_false" if phases else "none_no_auxiliary_variables"
    if legacy_phase_strategy == "solver_default":
        return [], "solver_default"

    # Random(0) generates a reproducible sign pattern. It does not configure a
    # Glucose3 random seed and the literals remain preferences, not assumptions.
    phase_rng = Random(0)
    phases = [
        variable if phase_rng.getrandbits(1) else -variable
        for variable in auxiliary_ids
    ]
    return (
        phases,
        "deterministic_aux_pattern" if phases else "none_no_auxiliary_variables",
    )


def decode_sat_model(model: list[int], n: int) -> list[tuple[int, int]]:
    """Decode true primary literals, ignoring auxiliaries, in row/column order."""
    primary_variables = primary_variable_count(n)
    return sorted(
        position_from_var(literal, n)
        for literal in model
        if 1 <= literal <= primary_variables
    )


def solve_cnf(
    n: int,
    cnf: list[list[int]],
    solver_name: str = "g3",
    total_variables: int | None = None,
    phase_policy: str = "solver_default",
    legacy_phase_strategy: str = "solver_default",
) -> dict[str, Any]:
    """Solve supplied CNF once; report SAT/UNSAT/UNKNOWN or invalid-model ERROR.

    Variable counts describe the reserved ID range, including the n*n primary
    variables. No encoding is performed here, so encoding is None and its time
    is zero. Unexpected solver exceptions propagate to the caller.
    """
    total_start = perf_counter()
    primary_variables = primary_variable_count(n)
    if solver_name != "g3":
        raise ValueError("Only Glucose3 (solver_name='g3') is supported")
    _validate_phase_configuration(phase_policy, legacy_phase_strategy)

    largest_variable = max((abs(lit) for clause in cnf for lit in clause), default=0)
    required_variables = max(primary_variables, largest_variable)
    if total_variables is None:
        total_variables = required_variables
    elif (
        not isinstance(total_variables, int)
        or isinstance(total_variables, bool)
        or total_variables < required_variables
    ):
        raise ValueError(f"total_variables must be an integer >= {required_variables}")

    positions: list[tuple[int, int]] | None = None
    valid: bool | None = None
    error: str | None = None
    decode_validate_time = 0.0

    load_start = perf_counter()
    with Glucose3(bootstrap_with=cnf) as solver:
        load_time = perf_counter() - load_start

        configuration_start = perf_counter()
        phase_literals, phase_override = _phase_configuration(
            primary_variables,
            total_variables,
            phase_policy,
            legacy_phase_strategy,
        )
        if phase_literals:
            solver.set_phases(phase_literals)
        configuration_time = perf_counter() - configuration_start

        search_start = perf_counter()
        sat_result = solver.solve()
        search_time = perf_counter() - search_start

        if sat_result is True:
            status = "SAT"
            decode_start = perf_counter()
            model = solver.get_model()
            if model is None:
                status = "ERROR"
                valid = False
                error = "Glucose3 returned SAT but did not provide a model"
            else:
                positions = decode_sat_model(model, n)
                valid = validate_positions(positions, n)
                if not valid:
                    status = "ERROR"
                    error = (
                        f"Decoded SAT model failed validate_positions: N={n}, "
                        f"decoded_queens={len(positions)}. Inspect positions for "
                        "queen count, bounds, row, column or diagonal conflicts."
                    )
            decode_validate_time = perf_counter() - decode_start
        elif sat_result is False:
            status = "UNSAT"
        else:
            status = "UNKNOWN"

        statistics = solver.accum_stats()

    result = {
        "method": "SAT",
        "solver": "Glucose3",
        "encoding": None,
        "n": n,
        "status": status,
        "has_solution": sat_result is True,
        "valid": valid,
        "positions": positions,
        "primary_variables": primary_variables,
        "auxiliary_variables": total_variables - primary_variables,
        "total_variables": total_variables,
        "clauses": len(cnf),
        "phase_policy": phase_policy,
        "phase_override": phase_override,
        "phase_literals": len(phase_literals),
        "encoding_time": 0.0,
        "load_time": load_time,
        "configuration_time": configuration_time,
        "search_time": search_time,
        "solve_time": load_time + search_time,
        "decode_validate_time": decode_validate_time,
        "statistics": statistics,
        "error": error,
    }
    result["total_time"] = perf_counter() - total_start
    return result


def solve_nqueens_pairwise(
    n: int,
    phase_policy: str = "legacy",
) -> dict[str, Any]:
    """Encode N-Queens with Pairwise, solve, and measure the complete operation."""
    total_start = perf_counter()
    cnf = encode_nqueens_pairwise(n)
    encoding_time = perf_counter() - total_start

    result = solve_cnf(
        n, cnf, "g3", total_variables=n * n, phase_policy=phase_policy
    )
    result["encoding"] = "pairwise"
    result["encoding_time"] = encoding_time
    result["total_time"] = perf_counter() - total_start
    return result


def solve_nqueens_binary(
    n: int,
    phase_policy: str = "legacy",
) -> dict[str, Any]:
    """Encode N-Queens with Binary, solve, and measure the complete operation."""
    total_start = perf_counter()
    cnf, total_variables = encode_nqueens_binary(n)
    encoding_time = perf_counter() - total_start

    result = solve_cnf(
        n, cnf, "g3", total_variables=total_variables, phase_policy=phase_policy
    )
    result["encoding"] = "binary"
    result["encoding_time"] = encoding_time
    result["total_time"] = perf_counter() - total_start
    return result


def solve_nqueens_sequential(
    n: int,
    phase_policy: str = "legacy",
) -> dict[str, Any]:
    """Encode N-Queens with Sequential, solve, and measure the complete operation."""
    total_start = perf_counter()
    cnf, total_variables = encode_nqueens_sequential(n)
    encoding_time = perf_counter() - total_start

    result = solve_cnf(
        n, cnf, "g3", total_variables=total_variables, phase_policy=phase_policy
    )
    result["encoding"] = "sequential"
    result["encoding_time"] = encoding_time
    result["total_time"] = perf_counter() - total_start
    return result


def solve_nqueens_commander(
    n: int,
    group_size: int = 3,
    phase_policy: str = "legacy",
) -> dict[str, Any]:
    """Encode with Commander, solve, and report its fixed grouping metadata."""
    total_start = perf_counter()
    cnf, total_variables = encode_nqueens_commander(n, group_size)
    encoding_time = perf_counter() - total_start

    result = solve_cnf(
        n, cnf, "g3", total_variables=total_variables, phase_policy=phase_policy
    )
    result["encoding"] = "commander"
    result["group_size"] = group_size
    result["encoding_time"] = encoding_time
    result["total_time"] = perf_counter() - total_start
    return result


def solve_nqueens_product(
    n: int,
    phase_policy: str = "legacy",
) -> dict[str, Any]:
    """Encode N-Queens with 2-Product and solve through the shared pipeline."""
    total_start = perf_counter()
    cnf, total_variables = encode_nqueens_product(n)
    encoding_time = perf_counter() - total_start

    result = solve_cnf(
        n,
        cnf,
        "g3",
        total_variables=total_variables,
        phase_policy=phase_policy,
        legacy_phase_strategy="deterministic_aux_pattern",
    )
    result["encoding"] = "product"
    result["encoding_time"] = encoding_time
    result["total_time"] = perf_counter() - total_start
    return result


def main(argv: list[str] | None = None) -> int:
    """Select an encoding; JSON mode takes precedence over board printing."""
    parser = argparse.ArgumentParser(description="Solve N-Queens with Glucose3")
    parser.add_argument("--n", type=int, required=True, help="Board size (n >= 1)")
    parser.add_argument(
        "--encoding",
        choices=("pairwise", "binary", "sequential", "commander", "product"),
        default="pairwise",
        help="CNF encoding (default: pairwise)",
    )
    parser.add_argument(
        "--phase-policy",
        choices=PHASE_POLICIES,
        default="legacy",
        help="Glucose3 phase policy (default: legacy compatibility)",
    )
    parser.add_argument("--json", action="store_true", help="Write one JSON result to stdout")
    parser.add_argument("--print-board", action="store_true", help="Print a valid SAT board")
    args = parser.parse_args(argv)

    try:
        solvers = {
            "pairwise": solve_nqueens_pairwise,
            "binary": solve_nqueens_binary,
            "sequential": solve_nqueens_sequential,
            "commander": solve_nqueens_commander,
            "product": solve_nqueens_product,
        }
        result = solvers[args.encoding](args.n, phase_policy=args.phase_policy)
    except Exception as exc:
        # The CLI reports exceptions explicitly; the Python API still raises them.
        error = {"n": args.n, "status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(error))
        else:
            print(error["error"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result))
    else:
        print(f"Solver: {result['solver']}")
        print(f"Encoding: {result['encoding'].capitalize()}")
        if "group_size" in result:
            print(f"Group size: {result['group_size']}")
        print(f"Phase policy: {result['phase_policy']}")
        print(f"Phase override: {result['phase_override']}")
        print(f"Phase literals: {result['phase_literals']}")
        print(f"N: {result['n']}")
        print(f"Status: {result['status']}")
        print(f"Valid: {result['valid']}")
        print(f"Primary variables: {result['primary_variables']}")
        print(f"Auxiliary variables: {result['auxiliary_variables']}")
        print(f"Variables: {result['total_variables']}")
        print(f"Clauses: {result['clauses']}")
        for label, key in (
            ("Encoding time", "encoding_time"),
            ("Load time", "load_time"),
            ("Configuration time", "configuration_time"),
            ("Search time", "search_time"),
            ("Solve time", "solve_time"),
            ("Decode/validation time", "decode_validate_time"),
            ("Total time", "total_time"),
        ):
            print(f"{label}: {result[key]:.9f} seconds")
        print(f"Statistics: {result['statistics']}")
        if result["error"] is not None:
            print(result["error"], file=sys.stderr)
        if args.print_board and result["valid"] is True:
            print_board(positions_to_board(result["positions"], args.n))

    if result["status"] == "ERROR":
        return 1
    if result["status"] == "UNKNOWN":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
