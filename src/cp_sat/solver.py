"""Solve N-Queens using OR-Tools CP-SAT and validate decoded positions."""

import argparse
import json
import sys
from time import perf_counter
from typing import Any

from ortools.sat.python import cp_model

from src.common.board import columns_to_positions, positions_to_board, print_board
from src.common.validator import validate_positions


def build_nqueens_model(n: int) -> tuple[cp_model.CpModel, list[cp_model.IntVar]]:
    """Build a CP-SAT model for N-Queens with integer decision variables."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")

    model = cp_model.CpModel()

    # Create decision variables: queens[row] = column
    queens = [model.new_int_var(0, n - 1, f"q_{row}") for row in range(n)]

    # Columns must be distinct
    model.add_all_different(queens)

    # Main diagonals must be distinct (row - column is constant along main diagonal, or column - row)
    model.add_all_different([queens[row] - row for row in range(n)])

    # Anti-diagonals must be distinct (row + column is constant)
    model.add_all_different([queens[row] + row for row in range(n)])

    return model, queens


def solve_nqueens_cp_sat(
    n: int,
    time_limit: float = 300.0,
    workers: int = 1,
    random_seed: int = 0,
) -> dict[str, Any]:
    """Solve N-Queens using CP-SAT, returning a standardized result dictionary."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")
    if time_limit <= 0:
        raise ValueError(f"time_limit must be > 0, got {time_limit}")
    if not isinstance(workers, int) or workers < 1:
        raise ValueError(f"workers must be an integer >= 1, got {workers}")

    total_start = perf_counter()

    build_start = perf_counter()
    model, queens = build_nqueens_model(n)
    build_time = perf_counter() - build_start

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = random_seed
    solver.parameters.log_search_progress = False

    solve_start = perf_counter()
    native_status_code = solver.solve(model)
    solve_time = perf_counter() - solve_start
    
    native_status = solver.status_name(native_status_code)
    
    # Map CP-SAT status to Project Status
    if native_status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status = "SAT"
        has_solution = True
    elif native_status_code == cp_model.INFEASIBLE:
        status = "UNSAT"
        has_solution = False
    elif native_status_code == cp_model.UNKNOWN:
        status = "UNKNOWN"
        has_solution = False
    elif native_status_code == cp_model.MODEL_INVALID:
        status = "ERROR"
        has_solution = False
    else:
        status = "ERROR"
        has_solution = False

    positions = None
    valid = None
    error = None
    decode_validate_time = 0.0

    if has_solution:
        decode_start = perf_counter()
        try:
            columns = [solver.value(q) for q in queens]
            positions = columns_to_positions(columns)
            valid = validate_positions(positions, n)
            if not valid:
                status = "ERROR"
                error = (
                    f"Decoded CP-SAT model failed validate_positions: N={n}, "
                    f"decoded_queens={len(positions)}."
                )
        except Exception as e:
            status = "ERROR"
            valid = False
            error = f"Error extracting CP-SAT solution: {e}"
        
        decode_validate_time = perf_counter() - decode_start

    if status == "ERROR" and error is None:
        error = f"CP-SAT returned unexpected status: {native_status}"

    # Extract statistics if available
    try:
        conflicts = solver.num_conflicts
    except AttributeError:
        conflicts = None

    try:
        branches = solver.num_branches
    except AttributeError:
        branches = None

    try:
        wall_time = solver.wall_time
    except AttributeError:
        wall_time = None

    result = {
        "method": "CP-SAT",
        "solver": "OR-Tools CP-SAT",
        "n": n,
        "status": status,
        "native_status": native_status,
        "has_solution": has_solution,
        "valid": valid,
        "positions": positions,
        "model_type": "integer_all_different",
        "decision_variables": n,
        "constraints": 3,
        "build_time": build_time,
        "solve_time": solve_time,
        "decode_validate_time": decode_validate_time,
        "time_limit": time_limit,
        "workers": workers,
        "random_seed": random_seed,
        "statistics": {
            "conflicts": conflicts,
            "branches": branches,
            "wall_time": wall_time,
        },
        "error": error
    }
    result["total_time"] = perf_counter() - total_start
    return result


def main(argv: list[str] | None = None) -> int:
    """Run CP-SAT N-Queens solver from command line."""
    parser = argparse.ArgumentParser(description="Solve N-Queens with OR-Tools CP-SAT")
    parser.add_argument("--n", type=int, required=True, help="Board size (n >= 1)")
    parser.add_argument("--time-limit", type=float, default=300.0, help="Time limit in seconds")
    parser.add_argument("--workers", type=int, default=1, help="Number of search workers")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Write one JSON result to stdout")
    parser.add_argument("--print-board", action="store_true", help="Print a valid CP-SAT board")
    args = parser.parse_args(argv)

    try:
        result = solve_nqueens_cp_sat(
            n=args.n,
            time_limit=args.time_limit,
            workers=args.workers,
            random_seed=args.random_seed
        )
    except Exception as exc:
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
        print(f"Method: {result['method']}")
        print(f"Model type: {result['model_type']}")
        print(f"N: {result['n']}")
        print(f"Status: {result['status']} (Native: {result['native_status']})")
        print(f"Valid: {result['valid']}")
        print(f"Decision variables: {result['decision_variables']}")
        print(f"Constraints: {result['constraints']}")
        print(f"Time limit: {result['time_limit']}")
        print(f"Workers: {result['workers']}")
        print(f"Random seed: {result['random_seed']}")
        for label, key in (
            ("Build time", "build_time"),
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
    sys.exit(main())
