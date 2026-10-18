# N-Queens SAT Encodings & Exact Solvers

A modular, reproducible Python framework implementing and evaluating propositional satisfiability (SAT) encodings and exact constraint solving paradigms on the classic N-Queens problem.

## 1. Overview

This repository provides complete, rigorously validated implementations of **five Boolean SAT At-Most-One (AMO) encodings** and **four exact solver baselines** (Constraint Programming and Mixed Integer Programming), paired with automated solution verification, process-isolated resource guards, and open benchmark datasets.

> **Note on Submission & Deliverables:** The comprehensive scientific paper (*A Reproducible Empirical Comparison of SAT Encodings and Exact Solvers for the N-Queens Problem*) is submitted separately as an independent document. All source code, solver wrappers, test suites, and experimental benchmark datasets are openly hosted directly within this repository.

### Implemented Methods

* **Boolean SAT Encodings (PySAT Glucose3 backend):**
  * `sat_pairwise`: Direct quadratic pairwise AMO encoding ($\Theta(N^3)$ total clauses, $0$ auxiliary variables).
  * `sat_binary`: Logarithmic bitwise AMO encoding ($\Theta(N^2 \log N)$ total clauses, $O(N \log N)$ auxiliary variables).
  * `sat_sequential`: Sinz's sequential unary counter AMO encoding ($\Theta(N^2)$ total clauses, $O(N^2)$ auxiliary variables).
  * `sat_commander`: Recursive group-of-3 commander AMO encoding ($\Theta(N^2)$ total clauses, $O(N^2)$ auxiliary variables).
  * `sat_product`: 2-Product grid AMO encoding ($\Theta(N^2)$ total clauses, $O(N^{1.5})$ auxiliary variables).
* **Exact Solver Baselines:**
  * `cp_sat`: Google OR-Tools CP-SAT (row-based integer representation with 3 global `AllDifferent` constraints).
  * `cplex_cp`: IBM CP Optimizer (Constraint Programming via DOcplex with 3 `all_diff` constraints).
  * `gurobi_mip`: Gurobi Optimizer (0-1 binary integer linear programming with $6N-6$ linear constraints).
  * `cplex_mip`: IBM CPLEX MIP (0-1 binary integer linear programming via DOcplex MP).

---

## 2. Project Structure

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
├── results/                # Complete published benchmark artifacts (see results/README.md)
│   ├── README.md           # Comprehensive dataset dictionary and mapping to paper tables/figures
│   ├── raw/                # Immutable trial logs (benchmark_nqueens_primary_full.jsonl, n200.jsonl)
│   ├── metadata/           # Execution environment telemetry, config fingerprints, preflight
│   ├── processed/          # Tabular CSV matrices and aggregated descriptive statistics
│   ├── tables/             # Publication-ready CSV tables matching paper tables (Table 2 to 8)
│   └── figures/            # Publication-ready vector PDF and PNG plots (Figures 2 to 9)
├── tests/                  # Unit, consistency, and integration tests (398 passing tests)
├── tests_large/            # Validation tests on large instances (N=100)
├── scripts/                # Verification utilities (e.g., Table 9 closed-form generator)
├── main.py                 # Unified CLI entry point
├── run_all.sh              # Full reproduction benchmark script
└── requirements.txt        # Python package dependencies
```

---

## 3. Installation & Requirements

### Environment Setup
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

### Commercial Solver Requirements & Community Limits
* **PySAT (Glucose3) & Google OR-Tools CP-SAT:** Fully open-source and unrestricted across all instance sizes.
* **Gurobi Optimizer:** Free Community Edition limits model size to 2,000 variables and 2,000 constraints ($N \ge 50$ is cleanly flagged as `BLOCKED_LICENSE`).
* **IBM CPLEX MIP:** Free Community Edition limits model size to 1,000 variables and 1,000 constraints ($N \ge 32$ is cleanly flagged as `BLOCKED_LICENSE`).
* **IBM CP Optimizer:** Free Community Edition enforces a search-space combination threshold ($2^{1000}$ combinations, which raises `LICENSE_ERROR` at $N=200$). If using `cplex_cp`, ensure the `cpoptimizer` binary provided by DOcplex is exposed on `PATH` (e.g. `export PATH="$(pwd)/.venv/bin:$PATH"`).

Run license preflight checks:
```bash
python -m experiments.check_mip_license_limits
```

---

## 4. Usage (CLI)

Run individual solvers directly with ASCII board visualization or structured JSON metrics:

```bash
# Run SAT with Binary encoding on N=8 and display board
python -m src.sat.solver --encoding binary --n 8 --print-board

# Run OR-Tools CP-SAT on N=50 with JSON metrics
python -m src.cp_sat.solver --n 50 --json

# Run IBM CP Optimizer on N=32 with JSON metrics
python -m src.cplex_cp.solver --n 32 --json

# Run Gurobi MIP on N=20 with JSON metrics
python -m src.gurobi.solver --n 20 --json

# Run IBM CPLEX MIP on N=20 with JSON metrics
python -m src.cplex_mip.solver --n 20 --json
```

All solvers return standardized metrics (`pipeline_total_time`, `solve_time`, `peak_memory_mb`, `positions`) and validate solutions against board conflict rules using `src.common.validator`.

---

## 5. Running Tests

The test suite covers encodings, correctness, cross-solver consistency, and process supervision:

```bash
# Run the complete test suite (398 tests, ~18 seconds)
pytest tests/

# Run large-instance validation tests (N=100)
pytest tests_large/
```

---

## 6. Experimental Results & Data Availability

All experimental datasets, metadata logs, and reproduction scripts are published directly in the repository under [`results/`](results/) (see [`results/README.md`](results/README.md) for full data dictionaries and schema definitions):

* **Primary Benchmark Raw Data ($N \le 100$):** [`results/raw/benchmark_nqueens_primary_full.jsonl`](results/raw/benchmark_nqueens_primary_full.jsonl)  
  Contains 513 records total (495 planned official trials: 430 `SAT`, 20 `TIMEOUT`, 45 `BLOCKED_LICENSE`; plus 18 warmup runs) across 11 problem sizes ($N \in \{4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100\}$), 9 methods, and 5 randomized repetitions.
* **Large-Scale Experiment Raw Data ($N = 200$):** [`results/raw/benchmark_nqueens_large_scale_n200.jsonl`](results/raw/benchmark_nqueens_large_scale_n200.jsonl)  
  Contains 45 scheduled trials (20 `SAT`, 5 `TIMEOUT`, 5 `LICENSE_ERROR`, 10 `BLOCKED_LICENSE`, 5 `NOT_RUN_RESOURCE_POLICY`). Accompanied by preflight environment telemetry in [`results/metadata/benchmark_nqueens_large_scale_n200_preflight.json`](results/metadata/benchmark_nqueens_large_scale_n200_preflight.json).
* **Tabular Summaries:** [`results/processed/`](results/processed/) and publication tables in [`results/tables/`](results/tables/).
* **Publication Figures:** High-resolution vector PDF and PNG figures in [`results/figures/`](results/figures/).

---

## 7. Inspecting & Reproducing Published Results

All tables and figures can be verified and regenerated directly from the published raw datasets **without executing any solvers**:

```bash
# 1. Validate data integrity of all 495 primary benchmark records
python -m experiments.visualization.data_validator

# 2. Fast validation mode (checks completeness without redrawing plots)
python -m experiments.visualization.generate_all_figures --validate-only

# 3. Validate and summarize large-scale N=200 records
python -m experiments.large_scale.runner --analyze

# 4. Regenerate all primary benchmark CSV tables and figures (Figures 2 to 7)
python -m experiments.visualization.generate_all_figures

# 5. Regenerate large-scale N=200 summary tables and figures (Figures 8 and 9)
python experiments/large_scale/analysis_n200.py

# 6. Verify closed-form formulas against CNF generators for Appendix Table 9
python scripts/generate_appendix_table.py
```

---

## 8. Executing New Benchmarks

To conduct new experimental runs without overwriting the frozen benchmark data, use isolated output paths:

### 8.1 Smoke and Pilot Tests
```bash
# Smoke test (N=4, 8; 1 repetition)
python -m experiments.benchmark_runner --mode smoke

# Pilot test (N in {4, 8, 16, 20, 31, 32, 44, 50, 64, 100}; 1 repetition)
python -m experiments.benchmark_runner --mode pilot
```

### 8.2 Custom Out-of-Tree Large-Scale Execution ($N=200$)
To run extreme-scale experiments on a new host or cluster while reflecting local CPU, available RAM, and license configurations:

```bash
# Step 1: Generate a fresh preflight plan reflecting the local host
python -m experiments.large_scale.runner --preflight \
  --preflight-file /tmp/n200_custom_preflight.json \
  --raw-file /tmp/n200_custom_raw.jsonl

# Step 2: Execute trials into custom paths using the local preflight plan
python -m experiments.large_scale.runner --run \
  --preflight-file /tmp/n200_custom_preflight.json \
  --raw-file /tmp/n200_custom_raw.jsonl \
  --meta-file /tmp/n200_custom_meta.json \
  --priority-only
```
