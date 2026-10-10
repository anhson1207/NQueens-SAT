# Data Quality Report

Experiment ID: `nqueens_primary_full`

Dataset readiness: **COMPLETE / PASSED**

Official records expected: 495
Official records found: 495
Missing records: 0

Duplicates: 0

Warm-up records excluded: Yes
SAT phase policy: `solver_default`
Timeouts: 300s (Internal), 330s (External process limit)

Solver configurations: 9 methods (SAT-Pairwise, SAT-Binary, SAT-Sequential, SAT-Commander, SAT-Product, OR-Tools CP-SAT, Gurobi MIP, CPLEX MIP, IBM CP Optimizer) across sizes N=4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100. Repetitions: 5.

Primary metric: Pipeline Total Time (seconds)

Successful runs: 430
Timeout runs: 20
Blocked license runs: 45
Environment errors: 0

Validation failures: None.

## Limitations
- Single hardware platform.
- Only five repetitions.
- N-Queens is one problem family.
- Solver configurations may affect runtime.
- Search behavior can be phase-sensitive (particularly SAT Product).
- License restrictions limit MIP coverage (CPLEX MIP blocked at N>=32, Gurobi MIP blocked at N>=50).
- Conditional runtime statistics for methods with timeouts (timeout=300s excluded from median statistics).
- Different model representations across SAT, MIP and CP.
