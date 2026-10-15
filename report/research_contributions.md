# Research Contributions

This study provides a controlled, empirical investigation into the comparative performance of exact solving methodologies on the N-Queens problem. The contributions are strictly observational and engineering-driven, aiming to provide a robust dataset rather than introducing novel algorithmic theories.

## 1. Engineering Contributions
- **Reproducible Benchmark Framework**: Developed an automated, subprocess-isolated, and strictly bounded Python benchmark framework capable of evaluating both Satisfiability (SAT) and exact mathematical programming solvers under uniform external conditions.
- **Cross-Paradigm Integration**: Successfully unified 5 distinct Boolean SAT encodings (Pairwise, Binary, Sequential, Commander, Product) alongside 4 major industry solvers (OR-Tools CP-SAT, Gurobi MIP, CPLEX MIP, and IBM CP Optimizer) behind a common execution, validation, and schema API.
- **Data Transparency**: Generated and published a comprehensive dataset consisting of 495 official trial executions, complete with fine-grained timing breakdowns, structural constraint metadata, and algorithmic success matrices.

## 2. Empirical Research Contributions
- **Structural Analysis of SAT Encodings**: Provided quantitative evidence that theoretically compact SAT transformations (such as the Sequential Counter or Product encoding) do not inherently yield faster Conflict-Driven Clause Learning (CDCL) resolution times compared to naive, clause-heavy approaches (like Pairwise) on placement constraints.
- **Identification of Search Pathologies**: Empirically documented extreme non-monotonic runtime behavior in the SAT-Product encoding under standard branching heuristics. The observation that intermediate problem constraints ($N \in [40, 64]$) timeout while exponentially larger bounds ($N=100$) resolve instantly highlights the unpredictability of CDCL search trajectories.
- **Cross-Paradigm Scalability Observations**: Established comparative baselines demonstrating that while native Constraint Programming (CP Optimizer) is highly dominant, specific Boolean models (SAT-Binary) can offer competitive runtimes at scale ($N=100$) despite massive Boolean initialization overheads.

## 3. Future Research Directions (Unverified Hypotheses)
The dataset exposes several behavioral anomalies that require future dedicated investigation:
- **Phase Policy Ablation**: The pathological failure of the Product encoding demands future experimentation manipulating the Glucose3 internal phase selection (`aux_false` vs `solver_default`) to definitively prove whether auxiliary variable branching causes the timeout.
- **Memory Profiling**: The rapid execution of the massive Pairwise model suggests memory contiguousness and high propagation speeds. Cache-miss profiling is required to substantiate this hypothesis.
