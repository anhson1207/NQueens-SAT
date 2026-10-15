# N-Queens SAT Encodings & Exact Solvers

A modular, reproducible Python framework implementing and comparing propositional satisfiability (SAT) encodings and exact constraint solving paradigms on the classic N-Queens problem.

## Overview

The repository provides clean implementations of **5 SAT At-Most-One (AMO) encodings** and **4 state-of-the-art exact solver baselines** (Constraint Programming and Mixed Integer Programming), paired with automated solution verification and benchmarking tools.

### Supported Solvers & Encodings

* **SAT Encodings (PySAT Glucose3 backend):**
  * `sat_pairwise`: Direct quadratic pairwise encoding ($\Theta(N^3)$ clauses, 0 aux variables).
  * `sat_binary`: Bitwise encoding ($\Theta(N^2 \log N)$ clauses, $O(N \log N)$ aux variables).
  * `sat_sequential`: Sinz's sequential unary counter ($\Theta(N^2)$ clauses, $O(N^2)$ aux variables).
  * `sat_commander`: Recursive group-of-3 commander encoding ($\Theta(N^2)$ clauses, $O(N^2)$ aux variables).
  * `sat_product`: 2-Product grid encoding ($\Theta(N^2)$ clauses, $O(N^{1.5})$ aux variables).
* **Exact Solvers:**
  * `cp_sat`: Google OR-Tools CP-SAT (3 global `AllDifferent` constraints).
  * `cplex_cp`: IBM CP Optimizer (Constraint Programming via DOcplex).
  * `gurobi_mip`: Gurobi MIP (0-1 binary formulation with $6N-6$ linear constraints).
  * `cplex_mip`: IBM CPLEX MIP (0-1 binary linear programming via DOcplex).

---

## Project Structure

```text
nqueens-sat/
├── src/
│   ├── common/             # Board representation, solution validator, result models
│   ├── sat/                # SAT formulations and 5 AMO encodings
│   │   └── encodings/      # pairwise, binary, sequential, commander, product
│   ├── cp_sat/             # Google OR-Tools CP-SAT solver
│   ├── cplex_cp/           # IBM CP Optimizer solver
│   ├── gurobi/             # Gurobi MIP solver
│   └── cplex_mip/          # IBM CPLEX MIP solver
├── experiments/
│   ├── benchmark_runner.py # Process-isolated benchmark execution engine
│   ├── solver_registry.py  # Unified solver registration and metadata
│   ├── configs.py          # Benchmark configurations
│   ├── visualization/      # Data processing, validation, and plotting scripts
│   └── large_scale/        # Extreme-scale (N=200) experiment runners
├── tests/                  # Unit, consistency, and integration tests (390+ tests)
├── tests_large/            # Validation tests on large instances (N=100)
├── scripts/                # Verification utilities (e.g., Table 9 generator)
├── main.py                 # Unified CLI entry point
├── run_all.sh              # Full reproduction benchmark script
└── requirements.txt        # Python package dependencies
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/anhson1207/NQueens-SAT.git
cd NQueens-SAT

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Usage (CLI)

Run individual solvers with ASCII board visualization or structured JSON output:

```bash
# Run SAT with Binary encoding on N=8 and display board
python -m src.sat.solver --encoding binary --n 8 --print-board

# Run OR-Tools CP-SAT on N=50 with JSON metrics
python -m src.cp_sat.solver --n 50 --json

# Run IBM CP Optimizer on N=32
python -m src.cplex_cp.solver --n 32 --json

# Run Gurobi MIP on N=20
python -m src.gurobi.solver --n 20 --json

# Run IBM CPLEX MIP on N=20
python -m src.cplex_mip.solver --n 20 --json
```

All solvers return standardized metrics (`pipeline_total_time`, `solve_time`, `peak_memory_mb`, `positions`) and validate solutions against board conflict rules using `src.common.validator`.

---

## Running Tests

The test suite covers encodings, correctness, consistency across solvers, and process supervision:

```bash
# Run the complete test suite
pytest tests/

# Run large-instance validation tests (N=100)
pytest tests_large/
```

---

## Commercial License Boundaries (Community Editions)

* **PySAT & OR-Tools CP-SAT:** Open-source, no size limits.
* **Gurobi Optimizer:** Free Community Edition limits problems to 2,000 variables / constraints ($N \ge 50$ is cleanly flagged as `BLOCKED_LICENSE`).
* **IBM CPLEX MIP:** Free Community Edition limits problems to 1,000 variables / constraints ($N \ge 32$ is cleanly flagged as `BLOCKED_LICENSE`).
* **IBM CP Optimizer:** Free Community Edition enforces search-space bounds ($2^{1000}$ combinations).

Run license preflight checks:
```bash
python -m experiments.check_mip_license_limits
```

---

## License

This project is licensed under the MIT License.
