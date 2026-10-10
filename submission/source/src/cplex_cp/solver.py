"""Solve N-Queens using IBM CP Optimizer via docplex.cp and validate decoded positions."""

import argparse
import json
import sys
from time import perf_counter
from typing import Any

import docplex.cp.model as cp
from docplex.cp.parameters import CpoParameters
from docplex.cp.utils import CpoException

from src.common.board import columns_to_positions, positions_to_board, print_board
from src.common.validator import validate_positions


def build_nqueens_model(n: int) -> tuple[cp.CpoModel, list]:
    """Build a DOcplex CP model for N-Queens with integer decision variables."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")

    model = cp.CpoModel(name=f"nqueens_cplex_cp_{n}")

    # Create integer decision variables: queens[row] = column
    queens = model.integer_var_list(n, 0, n - 1, "q")

    # Columns must be distinct
    model.add(model.all_diff(queens))

    # Main diagonals must be distinct (row - col is distinct)
    model.add(model.all_diff([queens[i] - i for i in range(n)]))

    # Anti-diagonals must be distinct (row + col is distinct)
    model.add(model.all_diff([queens[i] + i for i in range(n)]))

    return model, queens


def solve_nqueens_cplex_cp(
    n: int,
    time_limit: float = 300.0,
    workers: int = 1,
    random_seed: int = 0,
    log_output: bool = False,
) -> dict[str, Any]:
    """Solve N-Queens using CPLEX CP (IBM CP Optimizer), returning a standardized result dictionary."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")
    if time_limit <= 0:
        raise ValueError(f"time_limit must be > 0, got {time_limit}")
    if not isinstance(workers, int) or workers < 1:
        raise ValueError(f"workers must be an integer >= 1, got {workers}")
    if not isinstance(random_seed, int) or random_seed < 0:
        raise ValueError(f"random_seed must be an integer >= 0, got {random_seed}")

    total_start = perf_counter()

    # Default missing/error values
    status = "UNKNOWN"
    native_status = "UNKNOWN"
    search_status = "UNKNOWN"
    stop_cause = "UNKNOWN"
    has_solution = False
    valid = None
    positions = None
    error = None
    
    build_time = 0.0
    solve_time = 0.0
    decode_validate_time = 0.0

    stats = {}

    try:
        build_start = perf_counter()
        model, queens = build_nqueens_model(n)
        build_time = perf_counter() - build_start

        params = CpoParameters()
        params.TimeLimit = time_limit
        params.Workers = workers
        params.RandomSeed = random_seed
        params.LogVerbosity = "Normal" if log_output else "Quiet"

        solve_start = perf_counter()
        result = model.solve(params=params)
        solve_time = perf_counter() - solve_start
        
        native_status = str(result.get_solve_status())
        search_status = str(result.get_search_status())
        stop_cause = str(result.get_stop_cause())
        
        if native_status in ("Feasible", "Optimal"):
            status = "SAT"
        elif native_status == "Infeasible":
            status = "UNSAT"
        elif native_status == "Unknown":
            if "TimeLimit" in stop_cause or stop_cause == "SearchStopped":
                status = "TIMEOUT"
            else:
                status = "UNKNOWN"
        elif native_status == "JobFailed":
            status = "ERROR"
            error = f"CP Optimizer JobFailed: {stop_cause}"
        elif native_status == "JobAborted":
            status = "UNKNOWN"
            error = f"CP Optimizer JobAborted: {stop_cause}"
        else:
            status = "UNKNOWN"
            
        has_solution = result.is_solution()

        if has_solution:
            decode_start = perf_counter()
            try:
                columns = [int(result.get_value(queens[i])) for i in range(n)]
                positions = columns_to_positions(columns)
                valid = validate_positions(positions, n)
                if not valid:
                    status = "ERROR"
                    error = (
                        f"Decoded CPLEX CP model failed validate_positions: N={n}, "
                        f"decoded_queens={len(positions)}."
                    )
            except Exception as e:
                status = "ERROR"
                valid = False
                error = f"Error extracting CPLEX CP solution: {e}"

            decode_validate_time = perf_counter() - decode_start

        # Extract statistics
        try:
            infos = result.get_solver_infos()
            if infos:
                stats["branches"] = infos.get_number_of_branches()
                stats["fails"] = infos.get_number_of_fails()
                stats["solutions"] = result.get_info("NumberOfSolutions")
                stats["solver_time"] = infos.get_solve_time()
                stats["total_time_internal"] = infos.get_total_time()
                stats["memory_usage"] = infos.get_memory_usage()
        except Exception:
            pass

    except CpoException as e:
        msg = str(e)
        if "can not be executed" in msg.lower() or "not found" in msg.lower() or "executable" in msg.lower():
            status = "MISSING_CP_ENGINE"
            error = f"Missing CP engine or executable: {msg}"
        elif "license" in msg.lower() or "promotional" in msg.lower() or "limit" in msg.lower():
            status = "LICENSE_ERROR"
            error = f"License restriction: {msg}"
        elif "architecture" in msg.lower() or "format" in msg.lower():
            status = "ENVIRONMENT_ERROR"
            error = f"Unsupported architecture/binary: {msg}"
        else:
            status = "ERROR"
            error = f"CpoException: {msg}"
    except Exception as e:
        msg = str(e)
        if "license" in msg.lower() or "promotional" in msg.lower() or "limit" in msg.lower():
            status = "LICENSE_ERROR"
            error = f"License restriction: {msg}"
        else:
            status = "ERROR"
            error = f"Exception: {msg}"

    res_dict = {
        "method": "CPLEX CP",
        "solver": "IBM CP Optimizer",
        "n": n,
        "status": status,
        "native_status": native_status,
        "search_status": search_status,
        "stop_cause": stop_cause,
        "has_solution": has_solution,
        "valid": valid,
        "positions": positions,
        "model_type": "integer_all_different",
        "decision_variables": n,
        "constraints": 3,
        "build_time": build_time if build_time > 0 else None,
        "solve_time": solve_time if solve_time > 0 else None,
        "decode_validate_time": decode_validate_time if decode_validate_time > 0 else None,
        "time_limit": time_limit,
        "workers": workers,
        "random_seed": random_seed,
        "statistics": stats,
        "runtime_capability": "Available",
        "error": error
    }
    
    if status == "MISSING_CP_ENGINE":
        res_dict["runtime_capability"] = "Missing"
    elif status == "LICENSE_ERROR":
        res_dict["runtime_capability"] = "Community Limit Restricted"
    elif status == "ENVIRONMENT_ERROR":
        res_dict["runtime_capability"] = "Environment Error"
        
    res_dict["total_time"] = perf_counter() - total_start
    return res_dict


def main(argv: list[str] | None = None) -> int:
    """Run CPLEX CP N-Queens solver from command line."""
    parser = argparse.ArgumentParser(description="Solve N-Queens with CPLEX CP (IBM CP Optimizer)")
    parser.add_argument("--n", type=int, required=True, help="Board size (n >= 1)")
    parser.add_argument("--time-limit", type=float, default=300.0, help="Time limit in seconds")
    parser.add_argument("--workers", type=int, default=1, help="Number of search workers")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Write one JSON result to stdout")
    parser.add_argument("--print-board", action="store_true", help="Print a valid board")
    parser.add_argument("--log-output", action="store_true", help="Enable solver log output")
    args = parser.parse_args(argv)

    try:
        result = solve_nqueens_cplex_cp(
            n=args.n,
            time_limit=args.time_limit,
            workers=args.workers,
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
        print(f"Status: {result['status']} (Native: {result['native_status']} Stop: {result['stop_cause']})")
        print(f"Valid: {result['valid']}")
        if result.get("decision_variables") is not None:
            print(f"Integer variables: {result['decision_variables']}")
            print(f"AllDifferent constraints: {result['constraints']}")
        print(f"Time limit: {result['time_limit']}")
        print(f"Workers: {result['workers']}")
        print(f"Random seed: {result['random_seed']}")
        
        for label, key in (
            ("Build time", "build_time"),
            ("Solve time", "solve_time"),
            ("Decode/validation time", "decode_validate_time"),
            ("Total time", "total_time"),
        ):
            if result.get(key) is not None:
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
    if result["status"] in ("UNKNOWN", "MISSING_CP_ENGINE", "ENVIRONMENT_ERROR"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
