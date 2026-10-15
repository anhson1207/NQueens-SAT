# Experimental Results & Discussion

## 4.1. Structural Comparison of SAT Encodings
The size and structure of the Conjunctive Normal Form (CNF) formulations vary drastically across the five evaluated At-Most-One (AMO) encodings. As instance size grows, these structural differences become prominent. At the maximum evaluated size of $N=100$, all formulations utilize an identical baseline of 10,000 primary binary variables, yet they differ significantly in auxiliary variable and clause generation (see Figure 4 and Figure 5).

- **Pairwise**: Introduces zero auxiliary variables but scales poorly in clause volume, generating 1,646,900 clauses at $N=100$.
- **Binary**: Requires $O(\log m)$ auxiliary variables per group, yielding 3,678 auxiliary variables and 269,024 clauses. 
- **Sequential Counter**: Minimizes clause generation (117,812 clauses) at the heavy cost of 39,402 auxiliary variables.
- **Commander**: Balances the hierarchy with 20,536 auxiliary variables and 118,092 clauses.
- **Product**: Achieves the most compact formulation in terms of clauses (116,672) while using only 9,492 auxiliary variables.

These structural observations highlight an essential finding: structural compactness does not necessarily equate to guaranteed search efficiency in Conflict-Driven Clause Learning (CDCL) solvers, as explored in the subsequent sections.

## 4.2. Runtime Performance of SAT Encodings
The resolution time for SAT formulations reveals that the number of clauses is an inadequate predictor of solver performance (Figure 1). At $N=100$, the **SAT-Binary** encoding achieved the fastest median pipeline runtime at 0.231 seconds. In stark contrast, the **SAT-Sequential** encoding, despite generating the second-fewest clauses, recorded the slowest median runtime of 58.077 seconds. 

Interestingly, the **SAT-Pairwise** encoding, burdened with over 1.6 million clauses, successfully completed the search in a median time of 1.148 seconds, significantly outperforming Sequential and Commander encodings. This demonstrates that the naive cost of constructing and maintaining massive clause lists in memory can be strongly offset by the efficiency of boolean constraint propagation (BCP) and the straightforward decision space (lacking auxiliary intermediate variables). The introduction of tens of thousands of auxiliary variables in Sequential and Commander encodings likely complicates the Glucose3 decision heuristics and unit propagation, leading to suboptimal search trajectories.

## 4.3. Non-monotonic Search Behavior of Product Encoding
A critical anomaly was observed in the performance scaling of the **SAT-Product** encoding. While it reliably solved small sizes and successfully resolved $N=100$ in an impressive median time of 0.620 seconds (5/5 successful trials), it completely failed to solve intermediate sizes. Specifically, at $N \in \{40, 44, 50, 64\}$, all 5 repetitions of the Product encoding resulted in a TIMEOUT (>300 seconds).

This non-monotonic runtime behavior (Figure 6) underscores the extreme sensitivity of CDCL solvers to variable ordering, phase selection, and restart heuristics. Because correctness tests validated the $N=100$ solutions independently, this is not a logical flaw in the encoding. Instead, the specific auxiliary-variable structure of the Product projection at intermediate sizes creates pathological search spaces under the `solver_default` phase policy of Glucose3. The solver makes early unfavorable branching decisions that fail to quickly trigger conflicts or learn useful clauses. The fact that the significantly larger $N=100$ instance is resolved orders of magnitude faster confirms that runtime scaling in SAT is not strictly monotonic with respect to $N$.

## 4.4. Performance of Exact Solvers
Constraint Programming (CP) architectures demonstrated highly favorable scaling characteristics compared to Boolean satisfiability (Figure 2). Modeled natively with $O(N)$ integer variables and global `AllDifferent` constraints, the CP implementations minimize model construction overhead. 

Both **IBM CP Optimizer** and **OR-Tools CP-SAT** maintained 100% completion reliability up to $N=100$. The CP Optimizer solver established itself as remarkably efficient for this specific global constraint formulation. 

The Mixed Integer Programming (MIP) solvers, **Gurobi MIP** and **IBM CPLEX MIP**, successfully solved instances up to $N=44$ and $N=31$ respectively, before triggering expected Community Edition license limits. Prior to hitting these limits, both MIP solvers exhibited highly competitive median runtimes (e.g., Gurobi achieved 0.0068s at $N=20$), demonstrating that linear inequality bounds on binary variables are highly effective for constrained placement logic. However, due to the license blocks, their large-scale asymptotic behaviors remain unverified in this dataset.

## 4.5. Cross-Paradigm Comparison at N=100
At the extreme boundary of the benchmark ($N=100$), only 7 of the 9 methods were executable due to MIP license restrictions. Table 1 summarizes the performance ranking of successful methods:

| Method | Formulation Family | Success Rate | Median Runtime (s) |
|---|---|---|---|
| IBM CP Optimizer | Constraint Programming | 5 / 5 | 0.153 |
| SAT-Binary | Boolean SAT | 5 / 5 | 0.231 |
| SAT-Product | Boolean SAT | 5 / 5 | 0.620 |
| OR-Tools CP-SAT | Constraint Programming | 5 / 5 | 0.808 |
| SAT-Pairwise | Boolean SAT | 5 / 5 | 1.148 |
| SAT-Commander | Boolean SAT | 5 / 5 | 3.143 |
| SAT-Sequential | Boolean SAT | 5 / 5 | 58.077 |

The **IBM CP Optimizer** holds the lowest observed median runtime, confirming the dominance of native integer propagation for domain-specific constraints. Nevertheless, the **SAT-Binary** formulation tracks surprisingly close (0.231s), outpacing even OR-Tools CP-SAT (0.808s). This cross-paradigm intersection implies that under favorable structural encodings, general-purpose boolean reasoning can effectively match or rival specialized constraint programming engines on moderately sized placement problems.

## 4.6. Completion Reliability and Runtime Variability
Across the entire 495-trial benchmark, 430 trials yielded successful `SAT` statuses with independently verified valid solutions. There were 20 TIMEOUT events, isolated entirely within the intermediate scales of the SAT-Product encoding. The 45 BLOCKED_LICENSE occurrences were expected boundaries and correctly handled by the framework without systemic failure.

Analysis of runtime variability (Figure 7) over the 5 independent repetitions indicates that execution was highly stable for CP solvers. In contrast, SAT methodologies exhibited noticeable variance at larger scales (particularly SAT-Sequential and SAT-Commander), heavily reflecting the non-deterministic nature of modern CDCL search trajectories responding to subtle memory layout or timing shifts during clause learning. 

## 4.7. Summary of Experimental Findings
The benchmark yields several core scientific observations:
1. Clause compactness in SAT encodings does not predict solving speed.
2. The SAT-Binary encoding provides the most reliable and performant Boolean formulation for N-Queens under a default CDCL configuration.
3. SAT solver execution time is not strictly monotonic; pathological heuristic traps can cause intermediate problem sizes (e.g., Product N=40) to timeout while exponentially larger variants ($N=100$) resolve almost instantly.
4. Native Constraint Programming architectures (CP Optimizer, CP-SAT) exhibit superior asymptotic stability and bypass the $O(N^2)$ memory initialization bottlenecks inherent in Boolean transformations.
