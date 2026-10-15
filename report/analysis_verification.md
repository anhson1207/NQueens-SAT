# Analysis Verification Traceability

This document provides exact traceability for the quantitative claims made in the Experimental Results section against the published artifact dataset.

### Claim 1: Structural Counts at N=100
**Claim:** Pairwise generates 1,646,900 clauses with 0 auxiliary variables. Product generates 116,672 clauses with 9,492 auxiliary variables.
**Source:** `results/tables/table04_sat_structure_n100.csv` and `results/tables/table01_sat_n100.csv`
**Filter/Calculation:** Row `n=100`. Read columns `Clauses` and `Auxiliary Variables`.
**Verification Status:** PASS.

### Claim 2: IBM CP Optimizer is the fastest at N=100
**Claim:** IBM CP Optimizer has the lowest median pipeline runtime among all executable methods at N=100, at approximately 0.153 seconds.
**Source:** `results/tables/table02_exact_solver_summary.csv`
**Filter/Calculation:** Match `Method = IBM CP Optimizer`. Value in `Median Runtime at Largest SAT N`.
**Verification Status:** PASS.

### Claim 3: SAT-Binary Outperforms Other SAT Encodings at N=100
**Claim:** SAT-Binary achieves a median runtime of ~0.231s at N=100, faster than all other SAT encodings and OR-Tools CP-SAT (~0.808s).
**Source:** `results/tables/table01_sat_n100.csv` and `results/tables/table02_exact_solver_summary.csv`
**Filter/Calculation:** Compare `Median Runtime` for `SAT-Binary` against `OR-Tools CP-SAT` and others.
**Verification Status:** PASS.

### Claim 4: Product Non-monotonicity and Timeouts
**Claim:** SAT-Product times out (0/5 success) at N=40, 44, 50, 64, but succeeds (5/5 success) at N=100 in ~0.620s.
**Source:** `results/tables/table05_completion_status.csv`
**Filter/Calculation:** Filter `Method = SAT-Product`. Check `Successful Runs` and `Timeout Runs` at N=40, 44, 50, 64, 100.
**Verification Status:** PASS.

### Claim 5: Gurobi and CPLEX MIP License Limits
**Claim:** Gurobi MIP succeeds up to N=44 and is blocked by license at N=50. CPLEX MIP succeeds up to N=31 and is blocked at N=32.
**Source:** `results/tables/table05_completion_status.csv` and `results/tables/table02_exact_solver_summary.csv`
**Filter/Calculation:** Filter `Method = Gurobi MIP` and `Method = IBM CPLEX MIP`. Check transition from `Successful Runs = 5` to `License Blocked Runs = 5`.
**Verification Status:** PASS.

### Claim 6: Complete Dataset Reliability
**Claim:** Exactly 495 trials were executed. 430 resulted in SAT, 20 TIMEOUT, 45 BLOCKED_LICENSE.
**Source:** Derived from `results/processed/benchmark_nqueens_primary_full.csv`
**Filter/Calculation:** Sum of all `repetition` bounds across 11 $N$ sizes, 9 methods, 5 reps = 495.
**Verification Status:** PASS.
