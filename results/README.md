# N-Queens Experimental Benchmark Datasets & Results Guide

This directory contains the complete, frozen experimental benchmark datasets, environment telemetry, aggregated tabular summaries, and publication-ready figures for the N-Queens SAT encodings and exact solvers comparative study.

---

## 1. Overview & Dataset Scope

The experimental study evaluates five Boolean SAT At-Most-One (AMO) encodings (`sat_pairwise`, `sat_binary`, `sat_sequential`, `sat_commander`, `sat_product`) and four exact solver baselines (`cp_sat`, `cplex_cp`, `gurobi_mip`, `cplex_mip`) across two distinct benchmark suites:

### 1.1 Primary Full Benchmark ($N \le 100$)
* **Raw Artifact:** [`results/raw/benchmark_nqueens_primary_full.jsonl`](file:///Users/nguyenanhson/nqueens-sat/results/raw/benchmark_nqueens_primary_full.jsonl)
* **Scope:** 11 problem sizes: $N \in \{4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100\}$.
* **Repetitions:** 5 independent runs per method-instance pair, executed in randomized order per repetition.
* **Volume:** Exactly **513 records** total:
  * **495 planned official benchmark trials** ($11 \times 9 \times 5 = 495$).
  * **18 warmup trials** ($N=4$, 2 warmups $\times$ 9 methods = 18, flagged with `"is_warmup": true`).
* **Official Status Breakdown (495 trials):**
  * `SAT`: **430** successful solves (100% verified conflict-free by mathematical validator).
  * `TIMEOUT`: **20** runs exceeding the 300.0s solver time limit.
  * `BLOCKED_LICENSE`: **45** runs proactively intercepted due to commercial Community Edition size caps ($N \ge 50$ for Gurobi MIP; $N \ge 32$ for CPLEX MIP).
  * `Duplicates`: **0** | `Missing keys`: **0**.

### 1.2 Supplementary Large-Scale Experiment ($N = 200$)
* **Raw Artifact:** [`results/raw/benchmark_nqueens_large_scale_n200.jsonl`](file:///Users/nguyenanhson/nqueens-sat/results/raw/benchmark_nqueens_large_scale_n200.jsonl)
* **Scope:** Extreme-scale evaluation at $N = 200$ across all 9 methods.
* **Repetitions:** 5 scheduled runs per method ($9 \times 5 = 45$ trials).
* **Official Status Breakdown (45 trials):**
  * `SAT`: **20** completed solves (SAT-Binary: 5, SAT-Commander: 5, SAT-Product: 5, CP-SAT: 5).
  * `TIMEOUT`: **5** runs (SAT-Sequential: 5, hit external 330.0s watchdog limit).
  * `LICENSE_ERROR`: **5** runs (IBM CP Optimizer: 5, exceeded Community Edition $2^{1000}$ search-space limit).
  * `BLOCKED_LICENSE`: **10** runs (Gurobi MIP: 5, CPLEX MIP: 5, exceeded variable/constraint limits).
  * `NOT_RUN_RESOURCE_POLICY`: **5** runs (SAT-Pairwise: 5, proactively blocked by preflight memory policy; projected $>4.17$~GiB RAM vs. $798.34$~MiB safe headroom cap).
* **Preflight Telemetry & Hashes:** [`results/metadata/benchmark_nqueens_large_scale_n200_preflight.json`](file:///Users/nguyenanhson/nqueens-sat/results/metadata/benchmark_nqueens_large_scale_n200_preflight.json).

---

## 2. Directory Structure & File Manifest

```text
results/
├── README.md                                    # This documentation guide
├── raw/                                         # Immutable raw trial logs (JSON Lines)
│   ├── benchmark_nqueens_primary_full.jsonl     # Primary benchmark raw log (513 records)
│   ├── benchmark_nqueens_large_scale_n200.jsonl # Large-scale N=200 raw log (45 records)
│   ├── benchmark_nqueens_primary_pilot.jsonl    # Pilot exploratory runs (108 records)
│   ├── benchmark_nqueens_primary_smoke.jsonl    # Smoke test verification log (27 records)
│   ├── benchmark_pilot_initial.jsonl            # Initial prototype exploratory log (85 records)
│   └── mip_license_limits.json                  # Commercial MIP license limit boundary scan
├── metadata/                                    # Execution environment, config & preflight telemetry
│   ├── benchmark_nqueens_primary_full_metadata.json   # Full benchmark execution telemetry
│   ├── benchmark_nqueens_primary_full_config.json     # Configuration parameters and seeds
│   ├── benchmark_nqueens_large_scale_n200_preflight.json # Preflight host limits & SHA-256 hashes
│   ├── benchmark_nqueens_large_scale_n200_metadata.json  # Post-run large-scale verification metadata
│   ├── benchmark_nqueens_primary_pilot_metadata.json  # Pilot telemetry
│   ├── benchmark_nqueens_primary_pilot_config.json    # Pilot configuration
│   └── benchmark_nqueens_primary_smoke_metadata.json  # Smoke test metadata
├── processed/                                   # Tabular transformations and descriptive summaries
│   ├── benchmark_nqueens_primary_full.csv       # Flat tabular export of all 495 primary trials
│   ├── benchmark_summary_nqueens_primary_full.csv # Aggregated mean/median/std/min/max per configuration
│   ├── benchmark_nqueens_primary_pilot.csv      # Flat tabular export of pilot trials
│   ├── benchmark_summary_nqueens_primary_pilot.csv # Summary statistics of pilot trials
│   ├── benchmark_nqueens_primary_smoke.csv      # Flat tabular export of smoke trials
│   ├── benchmark_summary_nqueens_primary_smoke.csv # Summary statistics of smoke trials
│   └── mip_license_limits.csv                   # CSV matrix of MIP license boundary thresholds
├── tables/                                      # Publication-ready CSV tables matching paper tables
│   ├── table01_sat_n100.csv                     # Paper Table 3: SAT Encodings at N=100
│   ├── table02_exact_solver_summary.csv         # Paper Table 4 & 5: Exact Solvers across sizes
│   ├── table03_all_methods_n20.csv              # Paper Table 7: All 9 methods at N=20 intersection
│   ├── table04_sat_structure_n100.csv           # Detailed structural breakdown at N=100
│   ├── table05_completion_status.csv            # Completion status count matrix across configurations
│   ├── table06_experiment_configuration.csv     # Paper Table 2: Benchmark environment and parameters
│   ├── table07_large_scale_n200.csv             # Paper Table 8: N=200 scalability and resource status
│   └── table08_n100_vs_n200.csv                 # Comparative scaling from N=100 to N=200
├── figures/                                     # High-resolution vector (PDF) and bitmap (PNG) figures
│   ├── figure_captions.md                       # Comprehensive figure captions and interpretations
│   ├── full/                                    # Primary benchmark figures (Figures 2 to 7)
│   │   ├── fig01_sat_runtime_vs_n.{pdf,png}     # Paper Fig 3: SAT Runtime vs N (log-log)
│   │   ├── fig02_exact_solver_runtime_vs_n.{pdf,png} # Paper Fig 5: Exact Solvers Runtime vs N
│   │   ├── fig03_all_methods_n20.{pdf,png}      # Paper Fig 7: All 9 Methods at N=20
│   │   ├── fig04_sat_clause_growth.{pdf,png}    # SAT Clause Growth vs Theoretical Bounds
│   │   ├── fig05_sat_variable_overhead_n100.{pdf,png} # Paper Fig 2: SAT Variable Overhead at N=100
│   │   ├── fig06_completion_matrix.{pdf,png}    # Paper Fig 4: Solver Completion Matrix
│   │   ├── fig07_runtime_variability.{pdf,png}  # Paper Fig 6: Runtime Variability across 5 runs
│   │   ├── data_quality_report.md               # Automated data quality audit summary
│   │   └── figure_manifest.json                 # Manifest tracking generated figures and timestamps
│   └── large_scale_n200/                        # Supplementary N=200 figures (Figures 8 and 9)
│       ├── fig08_n100_vs_n200.{pdf,png}         # Paper Fig 8: N=100 vs N=200 Median Pipeline Time
│       └── fig09_n200_completion.{pdf,png}      # Paper Fig 9: N=200 Outcome Distribution
├── backup/                                      # Historical backups matching preflight provenance
│   ├── benchmark_nqueens_primary_full.jsonl     # Frozen copy of primary full log
│   ├── benchmark_nqueens_primary_full_config.json # Frozen copy of primary config
│   ├── benchmark_nqueens_primary_pilot.jsonl    # Frozen copy of pilot log
│   ├── benchmark_nqueens_primary_pilot_metadata.json # Frozen copy of pilot metadata
│   ├── benchmark_nqueens_primary_smoke.jsonl    # Frozen copy of smoke log
│   ├── benchmark_nqueens_primary_smoke_metadata.json # Frozen copy of smoke metadata
│   ├── benchmark_pilot_initial.jsonl            # Frozen copy of initial prototype log
│   └── recovery_manifest.txt                    # Recovery validation checksum manifest
└── recovery/                                    # Pre-resume data audit logs
    ├── full_pre_resume_validation.json          # Pre-run validation record integrity checks
    └── full_pre_resume_validation.md            # Human-readable pre-resume validation report
```

---

## 3. Mapping from Paper Tables & Figures to Artifacts

The following cross-reference maps all tables and figures presented in the scientific report (*NQueens-SAT Paper*) to their generating data files and reproduction scripts:

| Paper Element | Caption / Topic | Primary Source File | Generation Script / Source |
| :--- | :--- | :--- | :--- |
| **Table 1** | Problem formulation summary across paradigms | `report/paper/sections/03_methodology.tex` | Theoretical summary |
| **Table 2** | Experimental environment & parameters | `results/tables/table06_experiment_configuration.csv` | `experiments/visualization/export_tables.py` |
| **Table 3** | SAT encodings structural statistics at $N=100$ | `results/tables/table01_sat_n100.csv` | `experiments/visualization/export_tables.py` |
| **Table 4** | Median solving runtime across problem sizes ($N \le 100$) | `results/tables/table02_exact_solver_summary.csv` | `experiments/visualization/export_tables.py` |
| **Table 5** | Solver completion matrix and success rate | `results/tables/table05_completion_status.csv` | `experiments/visualization/export_tables.py` |
| **Table 6** | Sampled process-tree peak RSS memory | `results/processed/benchmark_nqueens_primary_full.csv` | Column `peak_memory_mb` |
| **Table 7** | All nine methods compared at $N=20$ | `results/tables/table03_all_methods_n20.csv` | `experiments/visualization/export_tables.py` |
| **Table 8** | Large-scale $N=200$ scalability & resource limits | `results/tables/table07_large_scale_n200.csv` | `experiments/large_scale/analysis_n200.py` |
| **Table 9** | Exact theoretical vs. generated structural counts | `report/paper/sections/09_appendix.tex` | `scripts/generate_appendix_table.py` |
| **Figure 1** | N-Queens board representation & conflict rules | `report/paper/sections/01_introduction.tex` | Conceptual diagram |
| **Figure 2** | SAT auxiliary variable overhead ($N=100$) | `results/figures/full/fig05_sat_variable_overhead_n100.pdf` | `experiments/visualization/plot_sat_structure.py` |
| **Figure 3** | SAT runtime vs. $N$ (log-log scale) | `results/figures/full/fig01_sat_runtime_vs_n.pdf` | `experiments/visualization/plot_sat_runtime.py` |
| **Figure 4** | Solver completion status matrix | `results/figures/full/fig06_completion_matrix.pdf` | `experiments/visualization/plot_completion_matrix.py` |
| **Figure 5** | Exact solver runtime vs. $N$ | `results/figures/full/fig02_exact_solver_runtime_vs_n.pdf` | `experiments/visualization/plot_exact_runtime.py` |
| **Figure 6** | Runtime variability across 5 repetitions | `results/figures/full/fig07_runtime_variability.pdf` | `experiments/visualization/plot_runtime_variability.py` |
| **Figure 7** | All nine methods at $N=20$ intersection | `results/figures/full/fig03_all_methods_n20.pdf` | `experiments/visualization/plot_all_methods.py` |
| **Figure 8** | Median pipeline runtime: $N=100$ vs. $N=200$ | `results/figures/large_scale_n200/fig08_n100_vs_n200.pdf` | `experiments/large_scale/analysis_n200.py` |
| **Figure 9** | Distribution of completion statuses at $N=200$ | `results/figures/large_scale_n200/fig09_n200_completion.pdf` | `experiments/large_scale/analysis_n200.py` |

---

## 4. Metric Definitions & Aggregation Rules

### 4.1 Timing Definitions
* **`pipeline_total_time`:** The standard, end-to-end execution time of the solver pipeline from problem specification to solution extraction. For SAT solvers, it includes CNF encoding, clause loading into the PySAT Glucose3 solver, and CDCL search. For CP/MIP solvers, it covers model compilation, solver parameter setup, search, and variable extraction. Excludes parent process interpreter startup and post-run validation.
* **`solve_time`:** Pure search time spent inside the native backend solver engine (CDCL Glucose3 solver, C++ CP-SAT search core, Gurobi C engine, CPLEX engine).
* **`model_build_time` / `encoding_time`:** Time spent constructing the mathematical model / generating CNF clauses in memory prior to solver invocation.
* **`process_wall_time`:** External elapsed wall-clock time measured by the parent process watchdog using `time.perf_counter()`. Includes subprocess creation, memory polling overhead, IPC, and teardown.

> [!IMPORTANT]
> **Independent Component Median Rule:**
> When reporting summary metrics across the 5 repetitions, medians are computed **independently** for each timing column (`pipeline_total_time`, `solve_time`, `model_build_time`). Total pipeline time is evaluated per-trial first, and the median is taken over those trial totals:
> $$\text{Median}(\text{Pipeline Total}) \neq \text{Median}(\text{Build Time}) + \text{Median}(\text{Solve Time})$$
> Component medians should not be expected to sum to the reported total median.

### 4.2 Memory Tracking Semantics
* **`peak_memory_mb`:** Sampled process-tree Resident Set Size (RSS) measured in mebibytes ($\text{MiB} = 2^{20}\text{ bytes}$).
* **Sampling Interval:** Polled every `0.1` seconds by `psutil` recursively summing parent and descendant processes.
* **Platform Characteristics:**
  * Memory is monitored via polling rather than Linux cgroups because kernel-level `setrlimit(RLIMIT_RSS)` is advisory and unenforced on macOS.
  * Polled sampling may miss short transient memory spikes between sampling intervals.
  * Pages shared via Copy-on-Write (CoW) between parent and child processes may be double-counted.

### 4.3 Outcome Status Taxonomy
* **`SAT`:** Solver completed and returned a queen placement that was independently verified as mutually non-attacking by `src.common.validator.validate_positions`.
* **`UNSAT`:** Problem proved unsatisfiable (holds only for $N=2$ and $N=3$).
* **`TIMEOUT`:** Solver exceeded the allotted runtime threshold (300.0s internal solver limit or 330.0s external watchdog).
* **`BLOCKED_LICENSE`:** Preflight or runner proactively intercepted the trial because problem size exceeded commercial Community Edition limits ($N \ge 50$ for Gurobi MIP; $N \ge 32$ for CPLEX MIP).
* **`LICENSE_ERROR`:** Runtime license limitation encountered during solving (IBM CP Optimizer search-space bound $2^{1000}$ exceeded at $N=200$).
* **`NOT_RUN_RESOURCE_POLICY`:** Preflight resource guard proactively blocked execution because projected allocation exceeded safe headroom limits (SAT-Pairwise at $N=200$ projected $>4.17$~GiB RAM vs. $798.34$~MiB safe cap).
* **`MONITORING_ERROR`:** Subprocess watchdog encountered an unrecoverable process monitoring error.

---

## 5. Verification & Reproduction Commands

All datasets can be validated and all analytical figures and tables can be reproduced directly from the frozen historical raw logs without executing any solvers:

```bash
# 1. Validate integrity of all 495 primary benchmark records
python -m experiments.visualization.data_validator

# 2. Fast validation mode (checks dataset completeness without redrawing plots)
python -m experiments.visualization.generate_all_figures --validate-only

# 3. Validate and summarize large-scale N=200 records
python -m experiments.large_scale.runner --analyze

# 4. Regenerate all primary benchmark CSV tables and figures (Figures 2-7)
python -m experiments.visualization.generate_all_figures

# 5. Regenerate large-scale N=200 summary tables and figures (Figures 8-9)
python experiments/large_scale/analysis_n200.py

# 6. Verify closed-form formulas against CNF generators for Appendix Table 9
python scripts/generate_appendix_table.py
```

---

## 6. Recorded Host Environment

The benchmark suite was executed under controlled hardware and software conditions recorded in `results/metadata/`:

* **Host Platform:** Apple M2 (8 cores: 4 performance + 4 efficiency), macOS 14.0 (Darwin 23.0.0), 16.00 GiB Unified Memory.
* **Runtime:** Python 3.13.7 (CPython 64-bit).
* **Library Versions:**
  * `python-sat`: `1.9.dev15` (Glucose3 backend)
  * `ortools`: `9.15.6755` (CP-SAT engine)
  * `gurobipy`: `13.0.3` (Gurobi Optimizer)
  * `docplex`: `2.32.264`
  * `cplex`: `22.2.0.1` (IBM ILOG CPLEX & CP Optimizer)
  * `psutil`: `7.2.2`
  * `numpy`: `2.5.3` | `pandas`: `3.0.6` | `matplotlib`: `3.11.2` | `seaborn`: `0.13.2`
* **Concurrency:** Strict single-threaded execution (`workers=1`, `threads=1`).
* **Random Seed:** Deterministic fixed seed (`random_seed=0`, schedule seed `1337`).
