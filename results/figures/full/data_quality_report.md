# Data Quality Report

Experiment ID: `nqueens_primary_full`

Dataset readiness: **PARTIAL / PENDING**

Official records expected: 495
Official records found: 269
Missing records: 226

Duplicates: 0

Warm-up records excluded: Yes
SAT phase policy: `solver_default`

Solver configurations: 9 methods (SAT-Pairwise, SAT-Binary, SAT-Sequential, SAT-Commander, SAT-Product, OR-Tools CP-SAT, Gurobi MIP, CPLEX MIP, IBM CP Optimizer) across sizes N=4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100.

Primary metric: Pipeline Total Time (seconds)

Successful runs: N/A (Dataset incomplete)
Timeout runs: N/A (Dataset incomplete)
Blocked license runs: N/A (Dataset incomplete)
Environment errors: N/A (Dataset incomplete)

Validation failures:
- Missing 226 records.
- Metadata file not found (`results/metadata/benchmark_nqueens_primary_full_metadata.json`).

## Limitations
- Single hardware platform.
- Only five repetitions.
- N-Queens is one problem family.
- Solver configurations may affect runtime.
- Search behavior can be phase-sensitive.
- License restrictions limit MIP coverage.
- Conditional runtime statistics for methods with timeouts.
- Different model representations across SAT, MIP and CP.
