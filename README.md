# N-Queens Solvers Benchmark

A comprehensive experimental framework and benchmark suite designed to compare propositional satisfiability (SAT) encodings and state-of-the-art exact constraint solving approaches on the classic N-Queens problem.

## Overview

The primary objective of this project is to model, solve, and benchmark the N-Queens problem across different mathematical formulations. By implementing a highly structured data collection framework, the project accurately measures and evaluates how different models (SAT, Constraint Programming, and Mixed Integer Programming) scale with increasing problem sizes (up to N=100) under strict reproducibility constraints.

## Formulations & Solvers

The project evaluates 9 distinct solving methods, categorized into two main families: Boolean SAT Encodings and Exact Solvers.

### 1. Boolean SAT Encodings (via PySAT Glucose3)
All SAT encodings map the problem into $O(N^2)$ primary binary variables representing queen positions, and utilize various At-Most-One (AMO) algorithms.
- **Pairwise / Binomial (`sat_pairwise`)**: Standard $O(N^2)$ pairwise clauses per group. No auxiliary variables.
- **Binary (`sat_binary`)**: Bitwise AMO encoding, requiring $O(\log N)$ auxiliary variables.
- **Sequential Counter (`sat_sequential`)**: Sinz's sequential counter AMO, requiring $O(N)$ auxiliary variables and clauses.
- **Commander (`sat_commander`)**: Recursive commander AMO (group size = 3).
- **2-Product (`sat_product`)**: Non-recursive AMO using a grid-based 2D projection.

### 2. Exact Solver Baselines
- **OR-Tools CP-SAT (`cp_sat`)**: Constraint Programming using $O(N)$ integer variables (`q[row] = col`) and 3 global `AllDifferent` constraints.
- **IBM CP Optimizer (`cplex_cp`)**: Constraint Programming formulation identical to CP-SAT, solved via IBM's DOcplex CP engine.
- **Gurobi MIP (`gurobi_mip`)**: Mixed Integer Programming using $O(N^2)$ binary variables and linear inequality constraints.
- **IBM CPLEX MIP (`cplex_mip`)**: Mixed Integer Programming formulation identical to Gurobi, solved via DOcplex MP.

## Benchmark Framework & Configurations

To guarantee fairness, integrity, and reproducibility, the benchmarking framework includes:
- **Process Isolation**: Every trial runs in an independent, clean subprocess to prevent memory leaks and cache sharing.
- **Strict Configuration**: 
  - `workers = 1` and `threads = 1` for all solvers.
  - Constant `random_seed = 0` (for solver behaviors).
  - 300-second strict internal time limit; 330-second external subprocess kill limit.
  - SAT phase policy is set to `solver_default`.
- **Config Fingerprinting**: The runner computes a SHA-256 fingerprint of the benchmark configuration. The framework refuses to resume a benchmark if the configuration fingerprint changes.
- **License Handling**: The framework proactively detects Gurobi (2,000 variables) and CPLEX (1,000 variables) Community Edition limits. Sizes exceeding the license limits gracefully yield a `BLOCKED_LICENSE` status without crashing the suite.
- **Data Validator**: A strict validation module (`experiments/visualization/data_validator.py`) ensures no duplicate run IDs, no missing trials, and enforces schema matching for every generated JSONL record.

## Setup & Installation

**Prerequisites:** Python 3.11 or later. macOS, Linux, or Windows.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies
python -m pip install -r requirements.txt

# 3. CPLEX CP Engine Setup (Important)
# The `cplex_cp` solver requires the `cpoptimizer` binary to be available in your PATH.
# The `docplex` pip package downloads it automatically, but you must expose it:
export PATH="$(pwd)/.venv/bin:$PATH"
```

## Reproducibility & CLI

### Running the Official Benchmark
The full benchmark suite evaluates all 9 methods across 11 sizes ($N \in \{4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100\}$) with 5 repetitions per configuration, totaling 495 trials.

```bash
# Execute the full benchmark pipeline
bash run_all.sh

# The script performs:
# - Pilot benchmark (small-scale warmup)
# - Full benchmark (generates results/raw/benchmark_nqueens_primary_full.jsonl)
```

The framework securely supports **resuming**. If interrupted, simply rerun the script, and it will pick up exactly where it left off based on the completed trials in the `.jsonl` file.

### Single Solver CLI
Each solver can be run individually for testing or inspection. Output can be printed visually or as JSON.

```bash
# SAT Sequential (N=8) visually printed
python -m src.sat.solver --encoding sequential --n 8 --print-board

# OR-Tools CP-SAT (N=100) outputting JSON
python -m src.cp_sat.solver --n 100 --json

# IBM CP Optimizer (N=50)
python -m src.cplex_cp.solver --n 50 --json
```

## Test Instructions

The project uses `pytest` for all unit and integration tests.

```bash
# Run the entire test suite (including validation, solvers, and utilities)
pytest tests/
```
