"""Solve N-Queens using Gurobi MIP and validate decoded positions."""

import argparse
import json
import sys
from time import perf_counter
from typing import Any

import gurobipy as gp
from gurobipy import GRB

from src.common.board import positions_to_board, print_board
from src.common.validator import validate_positions


def build_nqueens_model(n: int, env: gp.Env | None = None) -> tuple[gp.Model, gp.tupledict]:
    """Build a Gurobi MIP model for N-Queens with binary decision variables."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")

    model = gp.Model("nqueens", env=env)

    # Create binary decision variables: x[row, col] = 1 if queen is placed
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Row constraints: exactly one queen per row
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"row_{i}")

    # Column constraints: exactly one queen per column
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"column_{j}")

    # Diagonal constraints: at most one queen per diagonal
    main_diagonals: dict[int, list[Any]] = {}
    anti_diagonals: dict[int, list[Any]] = {}
    for row in range(n):
        for col in range(n):
            main_diagonals.setdefault(row - col, []).append(x[row, col])
            anti_diagonals.setdefault(row + col, []).append(x[row, col])

    for key, variables in sorted(main_diagonals.items()):
        if len(variables) >= 2:
            model.addConstr(gp.quicksum(variables) <= 1, name=f"main_diag_{key}")

    for key, variables in sorted(anti_diagonals.items()):
        if len(variables) >= 2:
            model.addConstr(gp.quicksum(variables) <= 1, name=f"anti_diag_{key}")

    model.update()
    return model, x


def solve_nqueens_gurobi(
    n: int,
    time_limit: float = 300.0,
    threads: int = 1,
    random_seed: int = 0,
    log_output: bool = False,
) -> dict[str, Any]:
    """Solve N-Queens using Gurobi MIP, returning a standardized result dictionary."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n}")
    if time_limit <= 0:
        raise ValueError(f"time_limit must be > 0, got {time_limit}")
    if not isinstance(threads, int) or threads < 1:
        raise ValueError(f"threads must be an integer >= 1, got {threads}")

    total_start = perf_counter()

    try:
        build_start = perf_counter()
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", int(log_output))
        env.start()

        model, x = build_nqueens_model(n, env=env)
        build_time = perf_counter() - build_start

        # Configure solver
        model.Params.TimeLimit = time_limit
        model.Params.Threads = threads
        model.Params.Seed = random_seed
        model.Params.OutputFlag = int(log_output)

        solve_start = perf_counter()
        model.optimize()
        solve_time = perf_counter() - solve_start

        native_status_code = model.Status

        # Map Gurobi status to Project Status
        has_solution = False
        try:
            sol_count = model.SolCount
        except AttributeError:
            sol_count = 0

        if native_status_code == GRB.OPTIMAL:
            status = "SAT" if sol_count > 0 else "UNSAT"
            has_solution = sol_count > 0
            if not has_solution:
                status = "UNSAT"
        elif native_status_code == GRB.INFEASIBLE:
            status = "UNSAT"
        elif native_status_code == GRB.TIME_LIMIT:
            status = "SAT" if sol_count > 0 else "TIMEOUT"
            has_solution = sol_count > 0
        elif native_status_code == GRB.SUBOPTIMAL:
            status = "SAT" if sol_count > 0 else "UNKNOWN"
            has_solution = sol_count > 0
        elif native_status_code in (GRB.INF_OR_UNBD, GRB.INTERRUPTED):
            status = "UNKNOWN"
        elif native_status_code == GRB.NUMERIC:
            status = "ERROR"
        else:
            status = "UNKNOWN"

        if native_status_code == GRB.OPTIMAL:
            native_status_str = "OPTIMAL"
        elif native_status_code == GRB.INFEASIBLE:
            native_status_str = "INFEASIBLE"
        elif native_status_code == GRB.TIME_LIMIT:
            native_status_str = "TIME_LIMIT"
        elif native_status_code == GRB.SUBOPTIMAL:
            native_status_str = "SUBOPTIMAL"
        elif native_status_code == GRB.INF_OR_UNBD:
            native_status_str = "INF_OR_UNBD"
        elif native_status_code == GRB.INTERRUPTED:
            native_status_str = "INTERRUPTED"
        elif native_status_code == GRB.NUMERIC:
            native_status_str = "NUMERIC"
        else:
            native_status_str = str(native_status_code)

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
                        if x[row, col].X > 0.5:
                            positions.append((row, col))

                positions.sort(key=lambda p: p[0])

                valid = validate_positions(positions, n)
                if not valid:
                    status = "ERROR"
                    error = (
                        f"Decoded Gurobi model failed validate_positions: N={n}, "
                        f"decoded_queens={len(positions)}."
                    )
            except Exception as e:
                status = "ERROR"
                valid = False
                error = f"Error extracting Gurobi solution: {e}"

            decode_validate_time = perf_counter() - decode_start

        try:
            node_count = model.NodeCount
        except Exception:
            node_count = None

        try:
            runtime = model.Runtime
        except Exception:
            runtime = None

        try:
            iter_count = model.IterCount
        except Exception:
            iter_count = None

        result = {
            "method": "Gurobi MIP",
            "solver": "Gurobi Optimizer",
            "n": n,
            "status": status,
            "native_status": native_status_str,
            "has_solution": has_solution,
            "valid": valid,
            "positions": positions,
            "model_type": "binary_mip",
            "binary_variables": model.NumBinVars,
            "continuous_variables": model.NumVars - model.NumBinVars - model.NumIntVars,
            "integer_variables": model.NumIntVars,
            "total_variables": model.NumVars,
            "linear_constraints": model.NumConstrs,
            "build_time": build_time,
            "solve_time": solve_time,
            "decode_validate_time": decode_validate_time,
            "time_limit": time_limit,
            "threads": threads,
            "random_seed": random_seed,
            "statistics": {
                "node_count": node_count,
                "solution_count": sol_count,
                "runtime": runtime,
                "iter_count": iter_count,
            },
            "error": error
        }

    except gp.GurobiError as e:
        if "size-limited" in str(e).lower() or "size limited" in str(e).lower():
            result = {
                "method": "Gurobi MIP",
                "solver": "Gurobi Optimizer",
                "n": n,
                "status": "LICENSE_ERROR",
                "native_status": "LICENSE_ERROR",
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
                "error": f"GurobiError: {e}"
            }
        else:
            raise e

    result["total_time"] = perf_counter() - total_start
    return result


def main(argv: list[str] | None = None) -> int:
    """Run Gurobi N-Queens solver from command line."""
    parser = argparse.ArgumentParser(description="Solve N-Queens with Gurobi MIP")
    parser.add_argument("--n", type=int, required=True, help="Board size (n >= 1)")
    parser.add_argument("--time-limit", type=float, default=300.0, help="Time limit in seconds")
    parser.add_argument("--threads", type=int, default=1, help="Number of search threads")
    parser.add_argument("--random-seed", type=int, default=0, help="Random seed")
    parser.add_argument("--json", action="store_true", help="Write one JSON result to stdout")
    parser.add_argument("--print-board", action="store_true", help="Print a valid SAT board")
    parser.add_argument("--log-output", action="store_true", help="Enable Gurobi log output")
    args = parser.parse_args(argv)

    try:
        result = solve_nqueens_gurobi(
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
        print(f"Status: {result['status']} (Native: {result['native_status']})")
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
            print(result["error"], file=sys.stderr)
            
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
