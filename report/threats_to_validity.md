# Threats to Validity

## 1. Internal Validity
Several factors could potentially influence the cause-effect conclusions drawn from the experimental data:
- **SAT Phase Policy Constraints**: To establish a fair algorithmic baseline, all Boolean SAT encodings were executed under the Glucose3 `solver_default` phase policy. However, modifying branching heuristics can radically alter search trajectories. The observed failure of the SAT-Product encoding at intermediate sizes may be an artifact of this specific heuristic rather than a fundamental flaw in the encoding's logic.
- **Timing Definitions**: The primary metric, *pipeline total time*, aggregates formulation construction, solver instantiation, search, and validation. While CP solvers have near-zero build time ($O(N)$), SAT encodings suffer structural initialization penalties ($O(N^2)$). Comparisons of raw algorithmic search speed are somewhat conflated with encoding initialization overhead in this metric.
- **Process Isolation Overhead**: Subprocess dispatch introduces milliseconds of operating system overhead. While negligible for large $N$, this OS interference can skew precise statistical interpretation for $N \le 8$, where actual search times are microsecond-scale.
- **Provenance Metadata Status**: The benchmark metadata (`benchmark_nqueens_primary_full_metadata.json`) indicates a `git_worktree_dirty` state and 269 legacy records operating without strict configuration fingerprints. While data structures were explicitly checked for consistency, these flags represent minor limitations in strict cryptographic provenance tracing.

## 2. External Validity
The generalizability of the experimental findings is limited by the problem scope:
- **Single Problem Domain**: The study evaluates strictly the N-Queens problem, a purely constraint-satisfaction placement problem lacking complex logical implications or a minimization objective. Conclusions regarding encoding efficiency (e.g., Pairwise vs. Sequential) do not universally generalize to other combinatorial domains like Planning or Scheduling.
- **Hardware Homogeneity**: The benchmark was conducted exclusively on a single macOS Apple Silicon ARM64 architecture. Memory bandwidth, CPU cache sizes, and branch prediction mechanisms inherent to this architecture may uniquely favor specific clause memory layouts (like Pairwise), which might exhibit different comparative metrics on standard x86_64 server infrastructures.
- **Restricted Instance Scaling**: The maximum evaluated instance size is $N=100$. Extrapolating asymptotic algorithmic complexity or runtime curves beyond this bound remains speculative, especially given the non-monotonic behaviors observed.

## 3. Construct Validity
The degree to which the metrics accurately measure the intended concepts must be qualified:
- **Clause Count as a Proxy for Complexity**: The study correctly demonstrates that structural compactness (fewer clauses) is not synonymous with solver efficiency. Therefore, assuming theoretical variable/clause counts equate to practical computational load is an invalid construct.
- **License Limitations vs. Algorithmic Failure**: The MIP solvers (Gurobi and CPLEX) triggered Community Edition variable limits, leading to `BLOCKED_LICENSE` statuses. This represents a commercial API limitation, not a computational or algorithmic failure of Mixed Integer Programming methodologies. It would be mathematically invalid to state that Gurobi is incapable of solving N=100.
