# NQueens-SAT Final Submission Manifest

## Components
- **`paper/`**: Contains the final compiled PDF (`nqueens_sat_paper.pdf`) and all LaTeX source files (Elsevier CAS-SC template).
- **`figures/`**: Contains all 9 scientific figures used in the report, categorized by full benchmark and N=200 large-scale supplement.
- **`tables/`**: Contains CSV exports of the tables displayed in the paper.
- **`source/`**: Contains the complete Python source code for the 9 solvers, the benchmarking framework, and the exhaustive test suite.
- **`README.md`**: Main project documentation.

## Version Information
- **Git Commit Hash**: `b4dcd68a5dd71792ec759615a0be0680abb545d2`
- **PDF SHA-256**: `97b933c9896ee34c6aec75916624934a83502679d5a1e5de4c4eb21678012240`

## Compilation Instructions
The paper utilizes the Elsevier `cas-sc` document class. It can be compiled locally using `tectonic`:
```bash
tectonic paper/main.tex
```
Alternatively, standard `pdflatex` or `xelatex` can be used provided the `cas-sc` bundle is installed.

## Reproducibility
To reproduce the primary N<=100 benchmark:
```bash
python experiments/benchmark_runner.py
```
To reproduce the N=200 large-scale experiment:
```bash
python -m experiments.large_scale.runner --run
```
All data exports and figures can be regenerated via `experiments/benchmark_statistics.py` and `experiments/large_scale/analysis_n200.py`.

## Known Limitations
- The SAT-Product encoding exhibits extreme sensitivity to the default Glucose3 phase policy at intermediate sizes.
- Execution of the N=200 supplement requires at least 4GB of free memory, and IBM CP Optimizer is artificially blocked by Community Edition search-space licenses at this scale.

