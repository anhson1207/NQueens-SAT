"""Solve N-Queens using IBM CPLEX MIP via DOcplex and validate decoded positions."""

import argparse
import json
import sys
from time import perf_counter
from typing import Any

from docplex.mp.model import Model
from docplex.mp.utils import DOcplexLimitsExceeded, DOcplexException

from src.common.board import positions_to_board, print_board
from src.common.validator import validate_positions


def build_nqueens_model(n: int) -> tuple[Model, dict]:
    """Build a DOcplex MIP model for N-Queens with binary decision variables."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")

    model = Model(name=f"nqueens_cplex_mip_{n}")

    # Create binary decision variables: x[row, col] = 1 if queen is placed
    x = model.binary_var_matrix(range(n), range(n), name="x")

    # Row constraints: exactly one queen per row
    for i in range(n):
        model.add_constraint(
            model.sum(x[i, j] for j in range(n)) == 1,
            ctname=f"row_{i}"
        )

    # Column constraints: exactly one queen per column
    for j in range(n):
        model.add_constraint(
            model.sum(x[i, j] for i in range(n)) == 1,
            ctname=f"column_{j}"
        )

    # Diagonal constraints: at most one queen per diagonal
    main_diagonals: dict[int, list[Any]] = {}
    anti_diagonals: dict[int, list[Any]] = {}
    for row in range(n):
        for col in range(n):
            main_diagonals.setdefault(row - col, []).append(x[row, col])
            anti_diagonals.setdefault(row + col, []).append(x[row, col])

    for key, variables in sorted(main_diagonals.items()):
        if len(variables) >= 2:
            model.add_constraint(
                model.sum(variables) <= 1,
                ctname=f"main_diag_{key}"
            )

    for key, variables in sorted(anti_diagonals.items()):
        if len(variables) >= 2:
            model.add_constraint(
                model.sum(variables) <= 1,
                ctname=f"anti_diag_{key}"
            )

    return model, x


def classify_cplex_status(status_code: int | None, status_text: str | None, has_solution: bool) -> str:
    """Map CPLEX status code to Project status."""
    if status_code in (101, 102):  # MIP optimal / MIP optimal tolerance
        return "SAT" if has_solution else "UNKNOWN"
    if status_code == 103:  # MIP infeasible
        return "UNSAT"
    if status_code == 107:  # Time limit exceeded, but integer solution exists
        return "SAT" if has_solution else "TIMEOUT"
    if status_code == 108:  # Time limit exceeded, no integer solution
        return "TIMEOUT"
    if status_code == 1016: # Community size limit
        return "LICENSE_ERROR"
    return "UNKNOWN"


def solve_nqueens_cplex_mip(
    n: int,
    time_limit: float = 300.0,
    threads: int = 1,
    random_seed: int = 0,
    log_output: bool = False,
) -> dict[str, Any]:
    """Solve N-Queens using CPLEX MIP, returning a standardized result dictionary."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")
    if time_limit <= 0:
        raise ValueError(f"time_limit must be > 0, got {time_limit}")
    if not isinstance(threads, int) or threads < 1:
        raise ValueError(f"threads must be an integer >= 1, got {threads}")
    if not isinstance(random_seed, int) or random_seed < 0:
        raise ValueError(f"random_seed must be an integer >= 0, got {random_seed}")

    total_start = perf_counter()

    try:
        build_start = perf_counter()
        model, x = build_nqueens_model(n)
        build_time = perf_counter() - build_start

        # Metrics
        binary_variables = model.number_of_binary_variables
        continuous_variables = model.number_of_continuous_variables
        integer_variables = model.number_of_integer_variables
        total_variables = model.number_of_variables
        linear_constraints = model.number_of_linear_constraints

        # Configure solver
        model.set_time_limit(time_limit)
        model.parameters.threads = threads
        model.parameters.randomseed = random_seed
        
        if not log_output:
            model.context.solver.log_output = False
            
        solve_start = perf_counter()
        solution = model.solve(log_output=log_output)
        solve_time = perf_counter() - solve_start
        
        details = model.solve_details
        status_code = details.status_code
        status_text = details.status
        
        has_solution = solution is not None
        status = classify_cplex_status(status_code, status_text, has_solution)

        positions = None
        valid = None
        error = None
        decode_validate_time = 0.0

        if has_solution:
            decode_start = perf_counter()
            try:
                positions = []
                for row in range(n):
                    for col in range(n):
                        if solution.get_value(x[row, col]) > 0.5:
                            positions.append((row, col))

                positions.sort(key=lambda p: p[0])
                valid = validate_positions(positions, n)
                if not valid:
                    status = "ERROR"
                    error = (
                        f"Decoded CPLEX model failed validate_positions: N={n}, "
                        f"decoded_queens={len(positions)}."
                    )
            except Exception as e:
                status = "ERROR"
                valid = False
                error = f"Error extracting CPLEX solution: {e}"

            decode_validate_time = perf_counter() - decode_start

        result = {
            "method": "CPLEX MIP",
            "solver": "IBM ILOG CPLEX",
            "n": n,
            "status": status,
            "native_status": status_text,
            "native_status_code": status_code,
            "has_solution": has_solution,
            "valid": valid,
            "positions": positions,
            "model_type": "binary_mip",
            "binary_variables": binary_variables,
            "continuous_variables": continuous_variables,
            "integer_variables": integer_variables,
            "total_variables": total_variables,
            "linear_constraints": linear_constraints,
            "build_time": build_time,
            "solve_time": solve_time,
            "decode_validate_time": decode_validate_time,
            "time_limit": time_limit,
            "threads": threads,
            "random_seed": random_seed,
            "statistics": {
                "nodes_processed": details.nb_nodes_processed if hasattr(details, 'nb_nodes_processed') else None,
                "solver_reported_time": details.time if hasattr(details, 'time') else None,
                "mip_relative_gap": details.mip_relative_gap if hasattr(details, 'mip_relative_gap') else None,
                "best_bound": details.best_bound if hasattr(details, 'best_bound') else None,
            },
            "runtime_capability": "Academic/Full" if n >= 32 and status != "LICENSE_ERROR" else "Community Limit Possible",
            "error": error
        }

    except DOcplexLimitsExceeded as e:
        # Expected Error 1016 Community Limit
        result = _build_license_error_result(n, time_limit, threads, random_seed, str(e), 1016)
    except DOcplexException as e:
        if "1016" in str(e):
            result = _build_license_error_result(n, time_limit, threads, random_seed, str(e), 1016)
        else:
            raise e
    except Exception as e:
        if "1016" in str(e):
            result = _build_license_error_result(n, time_limit, threads, random_seed, str(e), 1016)
        else:
            raise e
    finally:
        if 'model' in locals():
            try:
                model.end()
            except Exception:
                pass

    result["total_time"] = perf_counter() - total_start
    return result


def _build_license_error_result(n: int, time_limit: float, threads: int, random_seed: int, msg: str, code: int) -> dict:
    """Helper to construct result dictionary for license error."""
    return {
        "method": "CPLEX MIP",
        "solver": "IBM ILOG CPLEX",
        "n": n,
        "status": "LICENSE_ERROR",
        "native_status": "LICENSE_ERROR",
        "native_status_code": code,
        "has_solution": False,
        "valid": None,
        "positions": None,
        "model_type": "binary_mip",
        "binary_variables": None,
        "continuous_variables": None,
        "integer_variables": None,
        "total_variables": None,
        "linear_constraints": None,
        "build_time": None,
        "solve_time": None,
        "decode_validate_time": None,
        "time_limit": time_limit,
        "threads": threads,
        "random_seed": random_seed,
        "statistics": {},
        "runtime_capability": "Community Limit Detected",
        "error": {
            "category": "COMMUNITY_SIZE_LIMIT",
            "code": code,
            "message": msg
        }
    }


def main(argv: list[str] | None = None) -> int:
    """Run CPLEX N-Queens solver from command line."""
    parser = argparse.ArgumentParser(description="Solve N-Queens with CPLEX MIP")
    parser.add_argument("--n", type=int, required=True, help="Board size (n >= 1)")
    parser.add_argument("--time-limit", type=float, default=300.0, help="Time limit in seconds")
    parser.add_argument("--threads", type=int, default=1, help="Number of search threads")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Write one JSON result to stdout")
    parser.add_argument("--print-board", action="store_true", help="Print a valid board")
    parser.add_argument("--log-output", action="store_true", help="Enable solver log output")
    args = parser.parse_args(argv)

    try:
        result = solve_nqueens_cplex_mip(
            n=args.n,
            time_limit=args.time_limit,
            threads=args.threads,
            random_seed=args.random_seed,
            log_output=args.log_output
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
        print(f"Status: {result['status']} (Native: {result['native_status']} Code: {result.get('native_status_code')})")
        print(f"Valid: {result['valid']}")
        if result["total_variables"] is not None:
            print(f"Binary variables: {result['binary_variables']}")
            print(f"Total variables: {result['total_variables']}")
            print(f"Linear constraints: {result['linear_constraints']}")
        print(f"Time limit: {result['time_limit']}")
        print(f"Threads: {result['threads']}")
        print(f"Random seed: {result['random_seed']}")
        
        for label, key in (
            ("Build time", "build_time"),
            ("Solve time", "solve_time"),
            ("Decode/validation time", "decode_validate_time"),
            ("Total time", "total_time"),
        ):
            if result[key] is not None:
                print(f"{label}: {result[key]:.9f} seconds")
                
        print(f"Statistics: {result['statistics']}")
        
        if result["error"] is not None:
            print(f"Error: {result['error']}", file=sys.stderr)
            
        if args.print_board and result["valid"] is True and result["positions"] is not None:
            print_board(positions_to_board(result["positions"], args.n))

    if result["status"] == "ERROR":
        return 1
    if result["status"] == "LICENSE_ERROR":
        return 3
    if result["status"] == "UNKNOWN":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
