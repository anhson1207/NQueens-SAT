# N-Queens Solvers and Benchmark Suite

A modular, reproducible Python framework implementing and comparing propositional satisfiability (SAT) encodings and exact constraint solving paradigms on the classic N-Queens problem.

## 1. Overview

The N-Queens problem is a canonical combinatorial benchmark in computer science and artificial intelligence. This repository provides complete source code implementations for five Boolean SAT encodings and four state-of-the-art exact solver baselines (Constraint Programming and Mixed Integer Programming), along with an isolated, deterministically seeded benchmarking framework, complete raw datasets, processed summary tables, and research manuscripts (`report/paper/main.pdf`).

## 2. Problem Formulation

The N-Queens problem asks to place $N$ queens on an $N \times N$ chessboard such that no two queens attack each other along any row, column, main diagonal, or anti-diagonal.

- **Rows & Columns:** Enforced via Exactly-One (EO = At-Least-One $\land$ At-Most-One) constraints.
- **Diagonals:** Enforced via At-Most-One (AMO) constraints.

## 3. Implemented Solvers and Encodings

### Boolean SAT Encodings (PySAT Glucose3)
All SAT models instantiate $N^2$ primary Boolean decision variables $x_{i,j} \in \{0, 1\}$ (indicating queen placement at row $i$, column $j$) and enforce cardinality via different At-Most-One (AMO) strategies:

1. **Pairwise / Binomial (`sat_pairwise`)**: Generates quadratic clauses ($\Theta(m^2)$ per group, $\Theta(N^3)$ total: $C_{\text{pairwise}} = 2N + N^2(N-1) + \frac{N(N-1)(2N-1)}{3}$) with zero auxiliary variables.
2. **Binary / Bitwise (`sat_binary`)**: Maps variables to $\lceil \log_2 m \rceil$ shared auxiliary bits, producing $\Theta(m \log m)$ clauses per group and $\Theta(N^2 \log N)$ total clauses across the board.
3. **Sequential Counter (`sat_sequential`)**: Implements Sinz's unary counter with $m-1$ auxiliary variables and $3m-4$ clauses per group, yielding $4N^2 - 6N + 2$ auxiliaries and $\Theta(N^2)$ clauses total ($12N^2 - 22N + 12$).
4. **Commander (`sat_commander`)**: Recursively partitions literals into groups of $k=3$ with commander variables, yielding linear auxiliary variables and $\Theta(N^2)$ clauses across the board.
5. **2-Product (`sat_product`)**: Structures literals into a 2D $\lceil \sqrt{m} \rceil$ grid, bounding auxiliary variables to $O(\sqrt{m})$ per group and $\Theta(N^2)$ clauses across the board.

### Exact Solver Baselines
1. **OR-Tools CP-SAT (`cp_sat`)**: Constraint Programming model with $N$ integer variables $q_i \in \{0, \dots, N-1\}$ and three global `AllDifferent` constraints.
2. **IBM CP Optimizer (`cplex_cp`)**: Native CP formulation identical to CP-SAT, solved using IBM DOcplex CP Optimizer.
3. **Gurobi MIP (`gurobi_mip`)**: Mixed Integer Programming formulation over $N^2$ binary variables with $6N-6$ linear equations and inequalities.
4. **IBM CPLEX MIP (`cplex_mip`)**: 0-1 Integer Linear Programming formulation identical to Gurobi, solved using IBM DOcplex Mathematical Programming.

## 4. Technology Stack

- **Language:** Python 3.11+
- **SAT Solver:** PySAT (`python-sat`) with Glucose3 backend
- **Constraint Programming:** Google OR-Tools (`ortools`), IBM DOcplex (`docplex`)
- **Mixed Integer Programming:** Gurobi Optimizer (`gurobipy`), IBM CPLEX (`cplex`)
- **Testing & Quality Assurance:** `pytest`
- **Visualization Tools:** `matplotlib`, `pandas`, `seaborn`

## 5. Project Structure

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
│   ├── configs.py          # Benchmark configurations and fingerprinting
│   ├── visualization/      # Data processing, validation, and plotting scripts
│   └── large_scale/        # Extreme-scale (N=200) experiment runners
├── tests/                  # Unit and integration tests (380+ tests)
├── tests_large/            # Validation tests on large instances (N=100)
├── main.py                 # Unified CLI entry point
├── run_all.sh              # Full reproduction benchmark script
├── requirements.txt        # Python package dependencies
└── README.md
```

## 6. Installation & Environment Setup

### 1. Clone the repository
```bash
git clone https://github.com/anhson1207/NQueens-SAT.git
cd NQueens-SAT
```

### 2. Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. IBM CP Optimizer Setup (Optional)
If using `cplex_cp`, ensure the `cpoptimizer` binary provided by `docplex` is exposed on your `PATH`:
```bash
export PATH="$(pwd)/.venv/bin:$PATH"
```

## 7. Running Solvers (CLI)

You can run individual solvers directly using the unified CLI or dedicated module interfaces:

```bash
# Run SAT with Binary encoding on N=8 and print the board
python -m src.sat.solver --encoding binary --n 8 --print-board

# Run OR-Tools CP-SAT on N=50 with JSON output
python -m src.cp_sat.solver --n 50 --json

# Run IBM CP Optimizer on N=32
python -m src.cplex_cp.solver --n 32 --json

# Run Gurobi MIP on N=20
python -m src.gurobi.solver --n 20 --json

# Run IBM CPLEX MIP on N=20
python -m src.cplex_mip.solver --n 20 --json
```

All solvers return standardized JSON metrics containing status, pipeline time, solve time, memory, and solution placement array. Every returned solution is verified by the built-in mathematical validator (`src.common.validator.py`).

## 8. Running Tests

The test suite covers encodings, correctness, consistency across solvers, and data validation without requiring external benchmark artifacts:

```bash
# Run the complete test suite
pytest tests/

# Run large-scale validation tests
pytest tests_large/
```

## 9. Benchmark Reproduction

The benchmarking framework executes solvers under subprocess isolation with strict timeouts (300.0s internal, 330.0s OS watchdog) and fixed random seeds:

```bash
# Execute the primary benchmark workflow (smoke, pilot, full)
bash run_all.sh

# Execute the supplementary large-scale N=200 experiment
python -m experiments.large_scale.runner --preflight
python -m experiments.large_scale.runner --run
```

To regenerate analytical figures from benchmark outputs:
```bash
python -m experiments.visualization.generate_all_figures
```

### Data Availability & Experimental Provenance
All experimental artifacts are tracked directly inside this repository under the `results/` tree:
- **Primary Full Benchmark ($N \le 100$):** `results/raw/benchmark_nqueens_primary_full.jsonl` contains 513 records total (495 planned official trials: 430 SAT, 20 TIMEOUT, 45 BLOCKED_LICENSE; plus 18 warmup trials) across 9 solving methods. Run configurations and execution environments are recorded in `results/metadata/benchmark_nqueens_primary_full_metadata.json`.
- **Supplementary Large-Scale Benchmark ($N = 200$):** `results/raw/benchmark_nqueens_large_scale_n200.jsonl` contains 45 scheduled trials (20 SAT, 5 TIMEOUT, 5 LICENSE_ERROR, 10 BLOCKED_LICENSE, 5 NOT_RUN_RESOURCE_POLICY). The preflight environment telemetry, hardware rlimits, and source-tree SHA-256 fingerprints are preserved in `results/metadata/benchmark_nqueens_large_scale_n200_preflight.json`.
- **Historical Trial Validation:** An additional 269 legacy trial records from early framework iterations were validated via parameter and output consistency without altering original metadata hashes.
- **Processed Summary Matrices:** Aggregated CSV tables are available in `results/tables/` and `results/processed/`.

## 10. Licensing and Community Edition Limits

- **PySAT (Glucose3) & OR-Tools CP-SAT:** Open-source and free without problem-size restrictions.
- **Gurobi Optimizer:** Community Edition limits problem size to 2,000 variables and 2,000 constraints ($N \ge 50$ is gracefully flagged as `BLOCKED_LICENSE`).
- **IBM CPLEX MIP:** Community Edition limits problem size to 1,000 variables and 1,000 constraints ($N \ge 32$ is gracefully flagged as `BLOCKED_LICENSE`).
- **IBM CP Optimizer:** Community Edition enforces a search-space combination bound ($2^{1000}$ combinations, which aborts at $N=200$ with `LICENSE_ERROR`).

The framework includes preflight checks (`experiments/check_mip_license_limits.py`) to classify commercial license boundaries cleanly without failing the benchmark suite.

## 11. Acknowledgments & Repository Information

- **Reference & Prior Art:** Builds upon and extends foundational experimental ideas from [Duongsuny/nQueens-SAT](https://github.com/Duongsuny/nQueens-SAT) (2024) with expanded exact solvers (Gurobi, CPLEX, CP-SAT), rigorous multi-trial descriptive profiling, process-isolated memory guards, and open benchmark artifacts.
- **Repository:** [https://github.com/anhson1207/NQueens-SAT](https://github.com/anhson1207/NQueens-SAT)
- **Author:** Nguyen Anh Son
- **License:** MIT License
