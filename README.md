# N-Queens Exact Solvers

Course project for comparing SAT encodings and exact solving approaches on the N-Queens problem.

## Planned methods

SAT encodings:

- Pairwise / Binomial
- Binary
- Sequential Counter
- Commander
- Product

Exact solver baselines:

- CP-SAT
- Gurobi MIP
- CPLEX MIP
- CPLEX CP

## Project status

Board utilities, independent validation, SAT variable groups, all five planned
SAT encodings, and the shared PySAT/Glucose3 solver are implemented. Exact
solver baselines remain planned.

## Run from the project root

Requires Python 3.11 or later. Create `.venv` with `python3 -m venv .venv` if needed.

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.sat.solver --n 4 --print-board
python -m src.sat.solver --n 100
python -m src.sat.solver --n 100 --json
python -m src.sat.solver --encoding binary --n 4 --print-board
python -m src.sat.solver --encoding binary --n 100 --json
python -m src.sat.solver --encoding sequential --n 4 --print-board
python -m src.sat.solver --encoding sequential --n 100 --json
python -m src.sat.solver --encoding commander --n 4 --print-board
python -m src.sat.solver --encoding commander --n 100 --json
python -m src.sat.solver --encoding product --n 4 --print-board
python -m src.sat.solver --encoding product --n 100 --json
```

`--encoding` accepts `pairwise` (the default), `binary`, `sequential` or
`commander`, or `product`. Commander uses the fixed experiment setting
`group_size=3` and reports that setting in JSON and text output.
`--json` writes exactly one JSON object, including positions and raw solver
statistics, and takes precedence over `--print-board`. CNF is never printed.
A board is printed only when requested and the decoded solution is valid.
SAT and UNSAT exit with code 0, ERROR with code 1, and UNKNOWN with code 2.
Unexpected exceptions produce an error diagnostic (a small JSON error object
in JSON mode) and exit with code 1.

## Solver API and timing

`solve_cnf(n, cnf, solver_name="g3", total_variables=None, initial_phases=None)`
accepts prebuilt CNF. `initial_phases` is an optional Glucose3 branching-phase
preference and does not add assumptions or clauses.
It reports `encoding=None` and `encoding_time=0`. Variable counts describe
reserved IDs: at least `n*n` primary variables, with the upper ID inferred from
CNF or supplied explicitly. Auxiliary IDs are excluded when decoding queens.

`solve_nqueens_pairwise(n)` builds CNF with the existing Pairwise encoder and
returns the same result fields with `encoding="pairwise"` and measured encoding
time. `solve_nqueens_binary(n)`, `solve_nqueens_sequential(n)` and
`solve_nqueens_commander(n, group_size=3)` and `solve_nqueens_product(n)` use the
same solver, decoder, validator, result schema and timing definitions. Commander
alone adds `group_size` to its result metadata.
Results use dictionaries; no shared result class is required yet.

- `encoding_time`: only CNF construction.
- `load_time`: Glucose3 construction, clause loading and optional phase setup.
- `search_time`: only `solver.solve()`.
- `solve_time`: `load_time + search_time`.
- `decode_validate_time`: model retrieval, decoding and independent validation;
  zero when there is no SAT model to retrieve.
- `total_time`: elapsed time through result construction, starting before encoding
  in the wrapper, or on entry to `solve_cnf` for prebuilt CNF. Includes metadata
  processing, statistics retrieval and solver cleanup, so it can exceed the sum
  of the named phases. It excludes Python startup, JSON formatting and printing.

UNSAT and UNKNOWN have `positions=None`, `valid=None`, and `has_solution=False`.
If Glucose3 reports SAT but the queen positions fail validation, the result is
ERROR with `valid=False` and diagnostic details; `has_solution=True` preserves
the underlying SAT finding. UNKNOWN is never treated as UNSAT.

The engine API is documented in the [official PySAT documentation](https://pysathq.github.io/docs/html/api/solvers.html).

## Binary encoding

`encode_nqueens_binary(n)` returns `(cnf, total_variables)`. Rows and columns use
exactly-one (ALO followed by Binary AMO); diagonals use AMO only. Clause order is
rows, columns, main diagonals, then anti diagonals, without deduplication.

For a group of `m >= 2` originals, Binary AMO allocates `(m - 1).bit_length()`
bits and emits one implication per original per bit, using zero-based list
indices and the lowest bit first. Selecting an original forces its binary code.
Two selected originals force contradictory bit values; selecting none leaves
the bits unconstrained. Empty/singleton AMO groups use no clauses or bits.
Exactly-one rejects an empty group and uses one ALO clause for a singleton.

One `AuxiliaryVariableAllocator` starts at `n*n + 1` and serves all groups.
Standalone callers must reserve every original ID below the allocator's initial
`start_id`; the encoder rejects collisions, including previously allocated IDs.
Each group gets fresh bits. Auxiliary assignments never become queen positions.

Expected structural counts for this precise variant:

| N | Encoding | Primary | Auxiliary | Total variables | Clauses |
|---|---|---:|---:|---:|---:|
| 4 | Pairwise | 16 | 0 | 16 | 84 |
| 4 | Binary | 16 | 32 | 48 | 120 |
| 4 | Sequential | 16 | 42 | 58 | 116 |
| 4 | Commander | 16 | 20 | 36 | 104 |
| 4 | Product | 16 | 68 | 84 | 160 |
| 100 | Pairwise | 10,000 | 0 | 10,000 | 1,646,900 |
| 100 | Binary | 10,000 | 3,678 | 13,678 | 269,024 |
| 100 | Sequential | 10,000 | 39,402 | 49,402 | 117,812 |
| 100 | Commander | 10,000 | 20,536 | 30,536 | 118,092 |
| 100 | Product | 10,000 | 9,492 | 19,492 | 116,672 |

These counts do not predict solve time. Binary may use more clauses at small N.

## Sequential Counter encoding

`encode_nqueens_sequential(n)` returns `(cnf, total_variables)` and uses one
shared `AuxiliaryVariableAllocator`. For every AMO group of size `m >= 2`, the
selected Sinz variant allocates `m - 1` fresh chain variables and emits exactly
`3m - 4` clauses. It also uses this variant for `m = 2`, so that group has one
auxiliary and two clauses. Empty and singleton AMO groups allocate nothing.

Exactly-one places the shared ALO clause before Sequential AMO. Rows and columns
use exactly-one; both diagonal directions use AMO. Group order is rows, columns,
main diagonals, then anti diagonals. Original IDs must remain below the allocator's
initial start ID, and collisions are rejected before any new ID is allocated.

For this formulation, auxiliary variables are `4N² - 6N + 2`, total variables
are `5N² - 6N + 2`, and clauses are `12N² - 22N + 12` for `N >= 1`.

## Commander encoding

Commander AMO uses ordered groups of at most three variables. Groups of size two
or three use Pairwise AMO directly. A larger group allocates one fresh commander
for every consecutive subgroup, including a singleton final subgroup, adds local
Pairwise AMO and each forward implication `original -> commander`, then applies
the same algorithm recursively to the commander list. It does not add reverse
implications or diagonal ALO clauses.

The public encoder checks that original IDs remain below the allocator's initial
start ID before allocation. Recursive calls use the same allocator and accept the
commander IDs just allocated at the previous level. The N-Queens formulation uses
one allocator across rows, columns, main diagonals and anti diagonals.

## Product / 2-Product encoding

For an AMO group of size `m >= 2`, Product computes
`p = ceil(sqrt(m))` with integer arithmetic and `q = ceil(m/p)`. It allocates
all `p` auxiliary row variables first, followed by all `q` auxiliary column
variables. Original `x[i]` maps row-major to `(i // q, i % q)` and emits
`[-x[i], row[i // q]]` followed by `[-x[i], column[i % q]]`. Pairwise AMO is
then applied to the auxiliary rows and columns. There are no reverse
implications, auxiliary ALO clauses, empty-cell clauses, or recursive Product
levels.

Exactly-one places one ALO clause over the originals before Product AMO. The
N-Queens encoder uses one allocator for row exactly-one, column exactly-one,
main-diagonal AMO and anti-diagonal AMO in that order. The Product wrapper gives
Glucose3 deterministic seed-0 phase preferences for auxiliary variables only;
these preferences do not constrain the formula or encode a queen placement.

## Tests

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s tests_large -v
python -m unittest tests_large.test_n100_pairwise_solver -v
python -m unittest tests_large.test_n100_binary_solver -v
python -m unittest tests_large.test_n100_sequential_solver -v
python -m unittest tests_large.test_n100_commander_solver -v
python -m unittest tests_large.test_n100_product_solver -v
python -m compileall src tests tests_large
```

Binary semantic tests enumerate all original assignments for group sizes 1–5
and existentially enumerate auxiliary assignments, for both AMO and exactly-one.
Small integration tests cover N=1,2,3,4,5,8 and compare status and independently
validated solutions with Pairwise. The Binary N=100 structural test checks every
group's private auxiliary range, clauses and original-variable coverage.
Sequential semantic tests use Glucose3 assumptions for every original assignment
at group sizes 1–5, including nonconsecutive IDs. Its N=100 structural test checks
every private chain and every clause in the required deterministic order.
Commander tests independently implement the recursive counting recurrence and
check every partition, local Pairwise clause, forward implication and recursive
commander set at N=100.
Product tests exhaust all original assignments for AMO and exactly-one at sizes
1 through 7 using Glucose3 assumptions. They also cover nonconsecutive IDs,
same-row, same-column and different-coordinate conflicts, non-square grids,
exact clause order and independent N=100 grid reconstruction.

Run large tests sequentially: N=100 materializes 1,646,900 Pairwise clauses,
269,024 Binary clauses, 117,812 Sequential clauses, 118,092 Commander clauses,
or 116,672 Product clauses.
Only one large CNF is retained at a time.
All five encodings' integration tests run N=20, 50 and 100 in separate child processes,
each with a 300-second timeout covering encoding, loading and solving. A timeout
fails the test with TIMEOUT; a killed or failed process reports its actual exit
code and diagnostics. No fixed speed threshold is used. Printed timings are
individual test measurements, not a formal performance benchmark.

## Verified results after Prompt 06

Measured on macOS arm64, Python 3.13.7, python-sat 1.9.dev15 (Glucose3).
The full regular suite passed **156/156** tests; the full large suite passed
**33/33**, sequentially with a 300-second limit per solver child.
`compileall src tests tests_large` succeeded. All five requested CLI commands
were executed successfully; JSON was parsed and its solution independently
validated, and the old CLI still defaults to Pairwise.

Both encodings returned SAT with valid solutions for N=1,4,5,8,20,50,100,
and UNSAT with null positions/validation for N=2,3. No mismatched counts,
invalid solutions, timeouts or memory errors occurred.

The comparison below uses N=20,50,100 measurements from the final large-test
run and N=4 API measurements collected afterward. These are individual runs
with the same implementation and environment, not averages or a formal benchmark.
Counts were observed from generated CNF and checked against the formulas.
All times are actual seconds; `solve = load + search`.

| N | Encoding | Primary | Auxiliary | Total variables | Clauses | Status | Valid | Encoding (s) | Solve (s) |
|---|---|---:|---:|---:|---:|---|---|---:|---:|
| 4 | pairwise | 16 | 0 | 16 | 84 | SAT | true | 0.000045 | 0.000075 |
| 4 | binary | 16 | 32 | 48 | 120 | SAT | true | 0.000087 | 0.000064 |
| 20 | pairwise | 400 | 0 | 400 | 12,580 | SAT | true | 0.002721 | 0.003422 |
| 20 | binary | 400 | 466 | 866 | 7,296 | SAT | true | 0.002654 | 0.133006 |
| 50 | pairwise | 2,500 | 0 | 2,500 | 203,450 | SAT | true | 0.023380 | 0.040544 |
| 50 | binary | 2,500 | 1,536 | 4,036 | 57,244 | SAT | true | 0.016219 | 0.025201 |
| 100 | pairwise | 10,000 | 0 | 10,000 | 1,646,900 | SAT | true | 0.329054 | 0.338221 |
| 100 | binary | 10,000 | 3,678 | 13,678 | 269,024 | SAT | true | 0.085178 | 0.100865 |

Binary timing breakdown from the same measurements:

| N | Encoding (s) | Load (s) | Search (s) | Decode/validate (s) | Total (s) |
|---|---:|---:|---:|---:|---:|
| 4 | 0.000087 | 0.000050 | 0.000015 | 0.000007 | 0.000188 |
| 20 | 0.002654 | 0.001706 | 0.131299 | 0.000078 | 0.136634 |
| 50 | 0.016219 | 0.015155 | 0.010046 | 0.000243 | 0.048634 |
| 100 | 0.085178 | 0.081600 | 0.019265 | 0.000536 | 0.224116 |

Raw N=100 statistics from that large-test run:

- Pairwise: `restarts=2, conflicts=277, decisions=8211, propagations=38180`.
- Binary: `restarts=4, conflicts=328, decisions=9588, propagations=117046`.

The fewer Binary clauses do not establish a general speed advantage: for
example, Binary N=20 took longer than Pairwise in this run. No average, median
or general performance conclusion is inferred from these single observations.

Pairwise results completing the Prompt 05 verification (the small-N rows were
measured in the same API session as the N=4 comparison above; large-N rows are
from the final large suite):

| N | Primary/total variables | Auxiliary | Clauses | Status | Valid | Encoding (s) | Solve (s) | Total (s) |
|---|---:|---:|---:|---|---|---:|---:|---:|
| 1 | 1 | 0 | 2 | SAT | true | 0.000065 | 0.000097 | 0.000221 |
| 2 | 4 | 0 | 10 | UNSAT | null | 0.000027 | 0.000253 | 0.000369 |
| 3 | 9 | 0 | 34 | UNSAT | null | 0.000060 | 0.000150 | 0.000316 |
| 4 | 16 | 0 | 84 | SAT | true | 0.000045 | 0.000075 | 0.000196 |
| 5 | 25 | 0 | 170 | SAT | true | 0.000118 | 0.000088 | 0.000253 |
| 8 | 64 | 0 | 744 | SAT | true | 0.000175 | 0.000263 | 0.000537 |
| 20 | 400 | 0 | 12,580 | SAT | true | 0.002721 | 0.003422 | 0.007415 |
| 50 | 2,500 | 0 | 203,450 | SAT | true | 0.023380 | 0.040544 | 0.084666 |
| 100 | 10,000 | 0 | 1,646,900 | SAT | true | 0.329054 | 0.338221 | 0.836924 |

Files added for Prompt 06:

- `src/sat/encodings/aux_vars.py`
- `tests/test_binary_encoding.py`
- `tests/test_binary_integration.py`
- `tests_large/test_n100_binary_encoding.py`
- `tests_large/test_n100_binary_solver.py`

Files updated for Prompt 06: `src/sat/encodings/binary.py`, `src/sat/solver.py`,
and `README.md`. The solver now adds `solve_nqueens_binary()` and CLI selection
while retaining the shared `solve_cnf()` and `decode_sat_model()`.

Prompt 05 also added `tests/test_sat_solver.py`, `tests/test_pairwise_integration.py`
and `tests_large/test_n100_pairwise_solver.py`, and implemented the existing
`src/sat/solver.py` placeholder plus README instructions.
Board, validator, SAT model and Pairwise encoder files remain unchanged.

## Verified results after Prompt 07

Measured on macOS arm64 with Python 3.13.7 and python-sat 1.9.dev15. The full
regular suite passed **194/194** tests and the full large suite passed **39/39**
tests. Large solver cases ran sequentially, with a 300-second timeout for each
child. No invalid model, timeout, killed process or memory error occurred.

Sequential returned UNSAT for N=2 and N=3. It returned SAT with an independently
validated solution for N=1,4,5,8,20,50,100. Its N=100 model decoded to exactly
100 queens, ignoring auxiliary IDs 10,001 through 49,402.

The following are individual measured runs, not averages or a formal benchmark.
The N=4 rows were measured together after the test suites. N=20,50,100 are from
the final full large-suite run. Counts are generated values checked against the
encoding formulas; all times are seconds.

| N | Encoding | Primary | Aux | Total vars | Clauses | Status | Valid | Encoding | Load | Search | Solve | Total |
|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| 4 | Pairwise | 16 | 0 | 16 | 84 | SAT | true | 0.000053 | 0.000047 | 0.000015 | 0.000062 | 0.000164 |
| 4 | Binary | 16 | 32 | 48 | 120 | SAT | true | 0.000066 | 0.000045 | 0.000013 | 0.000059 | 0.000160 |
| 4 | Sequential | 16 | 42 | 58 | 116 | SAT | true | 0.000053 | 0.000043 | 0.000014 | 0.000057 | 0.000142 |
| 20 | Pairwise | 400 | 0 | 400 | 12,580 | SAT | true | 0.002686 | 0.002290 | 0.000899 | 0.003188 | 0.007062 |
| 20 | Binary | 400 | 466 | 866 | 7,296 | SAT | true | 0.002556 | 0.001603 | 0.125875 | 0.127478 | 0.130984 |
| 20 | Sequential | 400 | 1,482 | 1,882 | 4,372 | SAT | true | 0.001176 | 0.000926 | 0.012501 | 0.013428 | 0.015290 |
| 50 | Pairwise | 2,500 | 0 | 2,500 | 203,450 | SAT | true | 0.021943 | 0.035297 | 0.003209 | 0.038506 | 0.080582 |
| 50 | Binary | 2,500 | 1,536 | 4,036 | 57,244 | SAT | true | 0.011342 | 0.011453 | 0.007305 | 0.018758 | 0.036174 |
| 50 | Sequential | 2,500 | 9,702 | 12,202 | 28,912 | SAT | true | 0.007518 | 0.006129 | 1.204846 | 1.210975 | 1.223252 |
| 100 | Pairwise | 10,000 | 0 | 10,000 | 1,646,900 | SAT | true | 0.318073 | 0.294154 | 0.012920 | 0.307073 | 0.783273 |
| 100 | Binary | 10,000 | 3,678 | 13,678 | 269,024 | SAT | true | 0.055650 | 0.056296 | 0.018742 | 0.075037 | 0.169571 |
| 100 | Sequential | 10,000 | 39,402 | 49,402 | 117,812 | SAT | true | 0.027691 | 0.025061 | 39.295726 | 39.320787 | 39.366885 |

Glucose3 statistics for the Sequential large cases:

| N | Restarts | Conflicts | Decisions | Propagations |
|---|---:|---:|---:|---:|
| 20 | 3 | 901 | 1,614 | 92,277 |
| 50 | 4 | 18,453 | 24,077 | 4,678,053 |
| 100 | 6 | 139,057 | 172,554 | 70,674,327 |

Sequential has the fewest clauses at N=100 and substantially more auxiliary
variables. Its search was slower in this individual run, illustrating why clause
count alone does not predict SAT performance. No general speed conclusion is
drawn from one observation.

Prompt 07 added `tests/test_sequential_encoding.py`,
`tests/test_sequential_integration.py`,
`tests_large/test_n100_sequential_encoding.py` and
`tests_large/test_n100_sequential_solver.py`. It implemented the existing
`src/sat/encodings/sequential.py` placeholder and updated `src/sat/solver.py`
and this README. Pairwise, Binary, model, allocator, board and validator source
files remain unchanged.

## Verified results after Prompt 08

Measured on macOS arm64 with Python 3.13.7 and python-sat 1.9.dev15. The full
regular suite passed **231/231** tests and the full large suite passed **45/45**
tests. Large cases ran sequentially with a 300-second whole-process timeout.
There were no failures, timeouts, invalid models, killed processes or memory
errors. `compileall src tests tests_large` also completed successfully.

Commander semantic tests used Glucose3 assumptions for every original assignment
at sizes 1 through 7, nonconsecutive IDs `[2, 7, 11, 19, 25]`, and size 10 with
a singleton final group and two recursive levels. AMO and exactly-one both matched
their projected semantics. Commander returned UNSAT for N=2,3 and SAT with an
independently validated solution for N=1,4,5,8,20,50,100.

These are individual measured runs, not a formal benchmark. N=4 was measured in
one API session after the suites. N=20,50,100 for all four encodings came from the
same final full large-suite run. Counts are actual generated values checked by an
independent recursive reference counter. Times are seconds.

| N | Encoding | Aux | Clauses | Status | Valid | Encoding | Load | Search | Solve | Total |
|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|
| 4 | Pairwise | 0 | 84 | SAT | true | 0.000056 | 0.000042 | 0.000014 | 0.000057 | 0.000161 |
| 4 | Binary | 32 | 120 | SAT | true | 0.000068 | 0.000046 | 0.000013 | 0.000059 | 0.000164 |
| 4 | Sequential | 42 | 116 | SAT | true | 0.000052 | 0.000047 | 0.000014 | 0.000061 | 0.000145 |
| 4 | Commander | 20 | 104 | SAT | true | 0.000078 | 0.000039 | 0.000006 | 0.000044 | 0.000149 |
| 20 | Pairwise | 0 | 12,580 | SAT | true | 0.002650 | 0.002255 | 0.000908 | 0.003164 | 0.007017 |
| 20 | Binary | 466 | 7,296 | SAT | true | 0.002786 | 0.001646 | 0.125285 | 0.126931 | 0.130673 |
| 20 | Sequential | 1,482 | 4,372 | SAT | true | 0.001163 | 0.001032 | 0.012927 | 0.013959 | 0.015816 |
| 20 | Commander | 772 | 4,278 | SAT | true | 0.001741 | 0.001015 | 0.124479 | 0.125494 | 0.127925 |
| 50 | Pairwise | 0 | 203,450 | SAT | true | 0.023741 | 0.035333 | 0.003251 | 0.038585 | 0.082093 |
| 50 | Binary | 1,536 | 57,244 | SAT | true | 0.011452 | 0.011906 | 0.007235 | 0.019142 | 0.036626 |
| 50 | Sequential | 9,702 | 28,912 | SAT | true | 0.007527 | 0.005927 | 1.192445 | 1.198373 | 1.210400 |
| 50 | Commander | 5,014 | 28,726 | SAT | true | 0.011305 | 0.006649 | 0.520754 | 0.527403 | 0.542688 |
| 100 | Pairwise | 0 | 1,646,900 | SAT | true | 0.323337 | 0.295708 | 0.013800 | 0.309508 | 0.795046 |
| 100 | Binary | 3,678 | 269,024 | SAT | true | 0.057074 | 0.054719 | 0.017199 | 0.071918 | 0.157342 |
| 100 | Sequential | 39,402 | 117,812 | SAT | true | 0.026778 | 0.024790 | 39.441672 | 39.466462 | 39.511137 |
| 100 | Commander | 20,536 | 118,092 | SAT | true | 0.041992 | 0.027815 | 1.901474 | 1.929290 | 1.987724 |

Glucose3 statistics for Commander:

| N | Restarts | Conflicts | Decisions | Propagations |
|---|---:|---:|---:|---:|
| 20 | 2 | 6,831 | 8,528 | 558,345 |
| 50 | 5 | 11,636 | 17,006 | 2,405,959 |
| 100 | 11 | 18,696 | 50,856 | 7,185,228 |

Commander N=100 has 20,536 auxiliaries and 118,092 clauses, close to Sequential's
clause count with fewer auxiliaries. The measured search times differ substantially,
but one run is not enough to select a generally faster encoding.

Prompt 08 added `tests/test_commander_encoding.py`,
`tests/test_commander_integration.py`,
`tests_large/test_n100_commander_encoding.py` and
`tests_large/test_n100_commander_solver.py`. It implemented the existing
`src/sat/encodings/commander.py` placeholder and updated `src/sat/solver.py` and
this README. Pairwise, Binary, Sequential, model, allocator, board and validator
source files remain unchanged.

## Verified results after Prompt 09

Measured on macOS arm64 with Python 3.13.7 and python-sat 1.9.dev15. The final
regular suite passed **269/269** tests in 1.358 seconds, and the final large suite
passed **51/51** tests sequentially in 44.773 seconds. Each large solver child
had a 300-second whole-process timeout. Product returned UNSAT for N=2,3 and SAT
with an independently validated solution for N=1,4,5,8,20,50,100. At N=100 the
decoded model contained exactly 100 queens; auxiliary IDs 10,001 through 19,492
were ignored by the shared decoder.

The exhaustive Product tests fixed every original assignment with assumptions
for both AMO and exactly-one at sizes 1 through 7. Every result matched the
projected cardinality semantics. Structural tests independently reconstructed
every auxiliary grid, implication and Pairwise clause at N=100. The required
counts were observed exactly:

| N | Primary | Auxiliary | Total variables | Clauses |
|---|---:|---:|---:|---:|
| 4 | 16 | 68 | 84 | 160 |
| 20 | 400 | 854 | 1,254 | 4,520 |
| 50 | 2,500 | 3,454 | 5,954 | 29,430 |
| 100 | 10,000 | 9,492 | 19,492 | 116,672 |

The N=100 structural comparison for the five precise variants implemented in
this project is:

| Encoding | Primary | Auxiliary | Total variables | Clauses |
|---|---:|---:|---:|---:|
| Pairwise | 10,000 | 0 | 10,000 | 1,646,900 |
| Binary | 10,000 | 3,678 | 13,678 | 269,024 |
| Sequential | 10,000 | 39,402 | 49,402 | 117,812 |
| Commander | 10,000 | 20,536 | 30,536 | 118,092 |
| Product | 10,000 | 9,492 | 19,492 | 116,672 |

The following timings are individual measurements, not averages or a formal
benchmark. N=20,50,100 rows are from the same final full large-suite run; N=4
rows were measured together immediately afterward. All times are seconds and
`solve = load + search`.

| N | Encoding | Primary | Aux | Total vars | Clauses | Status | Valid | Encoding | Load | Search | Solve | Total |
|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| 4 | Pairwise | 16 | 0 | 16 | 84 | SAT | true | 0.000058 | 0.000052 | 0.000018 | 0.000070 | 0.000179 |
| 4 | Binary | 16 | 32 | 48 | 120 | SAT | true | 0.000071 | 0.000050 | 0.000015 | 0.000065 | 0.000175 |
| 4 | Sequential | 16 | 42 | 58 | 116 | SAT | true | 0.000055 | 0.000050 | 0.000016 | 0.000065 | 0.000155 |
| 4 | Commander | 16 | 20 | 36 | 104 | SAT | true | 0.000083 | 0.000056 | 0.000007 | 0.000063 | 0.000175 |
| 4 | Product | 16 | 68 | 84 | 160 | SAT | true | 0.000083 | 0.000061 | 0.000015 | 0.000076 | 0.000214 |
| 20 | Pairwise | 400 | 0 | 400 | 12,580 | SAT | true | 0.002481 | 0.002457 | 0.000941 | 0.003398 | 0.007100 |
| 20 | Binary | 400 | 466 | 866 | 7,296 | SAT | true | 0.002381 | 0.001677 | 0.124383 | 0.126060 | 0.129385 |
| 20 | Sequential | 400 | 1,482 | 1,882 | 4,372 | SAT | true | 0.002051 | 0.000952 | 0.012373 | 0.013325 | 0.016070 |
| 20 | Commander | 400 | 772 | 1,172 | 4,278 | SAT | true | 0.002666 | 0.001007 | 0.122230 | 0.123237 | 0.126582 |
| 20 | Product | 400 | 854 | 1,254 | 4,520 | SAT | true | 0.002079 | 0.001045 | 0.044801 | 0.045846 | 0.048613 |
| 50 | Pairwise | 2,500 | 0 | 2,500 | 203,450 | SAT | true | 0.022227 | 0.036357 | 0.003497 | 0.039854 | 0.082282 |
| 50 | Binary | 2,500 | 1,536 | 4,036 | 57,244 | SAT | true | 0.011485 | 0.011509 | 0.007192 | 0.018701 | 0.036332 |
| 50 | Sequential | 2,500 | 9,702 | 12,202 | 28,912 | SAT | true | 0.007407 | 0.005888 | 1.344503 | 1.350391 | 1.362977 |
| 50 | Commander | 2,500 | 5,014 | 7,514 | 28,726 | SAT | true | 0.013000 | 0.006823 | 0.509772 | 0.516595 | 0.533713 |
| 50 | Product | 2,500 | 3,454 | 5,954 | 29,430 | SAT | true | 0.007632 | 0.006634 | 1.032893 | 1.039527 | 1.051140 |
| 100 | Pairwise | 10,000 | 0 | 10,000 | 1,646,900 | SAT | true | 0.317944 | 0.287233 | 0.013375 | 0.300608 | 0.777228 |
| 100 | Binary | 10,000 | 3,678 | 13,678 | 269,024 | SAT | true | 0.057239 | 0.058356 | 0.019358 | 0.077714 | 0.163665 |
| 100 | Sequential | 10,000 | 39,402 | 49,402 | 117,812 | SAT | true | 0.047679 | 0.029986 | 35.634423 | 35.664409 | 35.733898 |
| 100 | Commander | 10,000 | 20,536 | 30,536 | 118,092 | SAT | true | 0.041805 | 0.027927 | 1.911070 | 1.938997 | 1.998116 |
| 100 | Product | 10,000 | 9,492 | 19,492 | 116,672 | SAT | true | 0.026230 | 0.025994 | 0.132361 | 0.158355 | 0.198524 |

Product Glucose3 statistics from that final large run were:

| N | Restarts | Conflicts | Decisions | Propagations |
|---|---:|---:|---:|---:|
| 20 | 2 | 2,648 | 3,738 | 290,823 |
| 50 | 3 | 19,961 | 29,251 | 5,500,635 |
| 100 | 6 | 2,205 | 20,517 | 938,570 |

An initial development run with Glucose3's default phases timed out on Product
N=50 after 300 seconds even though Product N=100 solved in about one second.
Deterministic seed-0 auxiliary phase preferences removed that search pathology;
they do not alter the CNF or force any original assignment. The final complete
suite had no timeout, invalid model, killed process or memory error. Clause and
variable counts alone therefore do not establish a generally faster encoding.

Prompt 09 added `tests/test_product_encoding.py`,
`tests/test_product_integration.py`,
`tests_large/test_n100_product_encoding.py` and
`tests_large/test_n100_product_solver.py`. It implemented
`src/sat/encodings/product.py`, added Product dispatch and optional Glucose3
phase preferences to `src/sat/solver.py`, and updated this README. Pairwise,
Binary, Sequential, Commander, model, allocator, board and validator source
files remain unchanged.

## SAT Framework Validation

### Overview
This step represents a comprehensive audit of the SAT framework, confirming that all five planned encodings are fully integrated, consistent in their interfaces, and correct.

1. **Pairwise**: Standard binomial/pairwise AMO.
2. **Binary**: Bitwise AMO encoding.
3. **Sequential**: Sinz sequential counter AMO.
4. **Commander**: Recursive commander AMO (`group_size=3`).
5. **Product**: 2-Product non-recursive AMO.

### Structural Counts (N=100)
Every encoding was run with N=100, and the exact structural statistics were observed and validated:

| Encoding | Primary | Auxiliary | Total Variables | Clauses |
|---|---:|---:|---:|---:|
| Pairwise | 10,000 | 0 | 10,000 | 1,646,900 |
| Binary | 10,000 | 3,678 | 13,678 | 269,024 |
| Sequential | 10,000 | 39,402 | 49,402 | 117,812 |
| Commander | 10,000 | 20,536 | 30,536 | 118,092 |
| Product | 10,000 | 9,492 | 19,492 | 116,672 |

### Correctness Test Results
A cross-encoding regression test confirmed that all five encodings return the exact same expected satisfiability status across various board sizes:
- N=1, 4, 5, 8: SAT and independently validated valid queen positions.
- N=2, 3: UNSAT.

### Large-instance Test Results
The comprehensive `test_n100_all_encodings.py` test ran N=100 sequentially for all encodings with an independent 300-second timeout. All returned SAT with 100 correctly validated queens. Variables and clauses perfectly matched expected counts.

### Timing Definitions
The exact timing definitions are consistently implemented across all encodings:
- `encoding_time`: Time to build CNF.
- `load_time`: Glucose3 solver instantiation and clause loading.
- `search_time`: Pure `solver.solve()` execution time.
- `solve_time`: `load_time + search_time`.
- `decode_validate_time`: Model extraction and independent position validation.
- `total_time`: End-to-end execution, including all steps from start to finish. None of the encoders performs hidden additional work outside these metrics.

### Solver Configuration Audit
The `solve_cnf` API supports different phase policies to govern the solver's phase selection heuristic:
- `solver_default`: Uses Glucose3's out-of-the-box heuristic without `set_phases()`.
- `aux_false`: Prioritizes `False` for all auxiliary variables (for all encodings, where applicable).
- `legacy`: Preserves historical behavior per encoding for regression stability (default).

**Product's Phase Setting**:
Under the `legacy` policy, Product applies a deterministic random phase preference (seed 0) to its auxiliary variables. This strategy proved necessary to circumvent a severe search pathology that causes timeouts on standard Glucose3 configurations (e.g. N=50 timeout). These are strict phase *preferences* (using `solver.set_phases()`), not *assumptions*, so they don't alter the CNF logic or constrain any primary queen variables. However, this means Product's search is currently configured differently from the other four encodings (which use `solver_default` behavior when `legacy` is selected).

### Sanity Check
A standalone sanity check script is available to rapidly test encodings:
```bash
python -m experiments.sanity_check_sat --n 4 100
```
This runs the encodings in isolated subprocesses and displays a unified results table.

### Limitations
As discovered during the audit, the differing solver configurations (specifically the `legacy` phase policy giving an edge to Product vs. default for others) makes it unfair to compare search runtimes purely based on the encoding algorithm. To perform a fair, formal statistical benchmark, a unified configuration (e.g., `aux_false` or `solver_default` applied uniformly) must be used. Current runtime measurements conflate both encoding efficiency and solver configuration effects.

## OR-Tools CP-SAT Baseline

### Formulation
Unlike the Boolean SAT encodings which require $N^2$ binary variables to represent queen positions, the CP-SAT model natively leverages Constraint Programming integer variables:
1. **Decision Variables**: $N$ integer variables `q[row]`, where each variable represents the column containing the queen in that row. The domain of each variable is `[0, N-1]`.
2. **Constraints**:
   - `AllDifferent(q)`: No two queens can be in the same column.
   - `AllDifferent(q[row] - row)`: No two queens can be on the same main diagonal.
   - `AllDifferent(q[row] + row)`: No two queens can be on the same anti-diagonal.
3. **Objective**: None. The model strictly searches for a single feasible solution.

Because each row is assigned exactly one column variable, the requirement that each row contains exactly one queen is implicitly satisfied.

### Solver Configuration
- **Workers**: 1 (to ensure consistent deterministic search environments during evaluation).
- **Time limit**: 300.0 seconds.
- **Random seed**: 0.

### Status Mapping
The CP-SAT solver's native statuses are gracefully mapped to the common project schemas:
- `OPTIMAL` or `FEASIBLE` $\rightarrow$ `SAT` (a valid solution is found).
- `INFEASIBLE` $\rightarrow$ `UNSAT` (proof that no solution exists).
- `UNKNOWN` $\rightarrow$ `UNKNOWN` (solver timed out or gave up without proof).
- `MODEL_INVALID` $\rightarrow$ `ERROR`.

### Timing Definitions
The CP-SAT model follows standard timing conventions but with terminology distinct from Boolean encodings:
- `build_time`: Time to construct the `CpModel`, configure `N` variables, and assert the three `AllDifferent` constraints.
- `solve_time`: Wall-clock time of `solver.solve(model)`, representing all OR-Tools internal search mechanics (presolve, propagation, search).
- `decode_validate_time`: Converting integer variables into grid positions and passing them to the common validator.
- `total_time`: End-to-end framework execution time.

*Note: CP-SAT `solve_time` encompasses different operations compared to Glucose3's `search_time`, making direct sub-metric comparisons uneven. Benchmark conclusions should focus primarily on `total_time`.*

### Test Results

Tested on macOS arm64, Python 3.13.7, OR-Tools 9.11+. 

CP-SAT successfully found validated solutions (`SAT`) for $N=1, 4, 5, 8, 20, 50, 100$ and proved `UNSAT` for $N=2, 3$. All unit tests (model, constraints, configuration) and integration tests passed. 

#### CP-SAT Mathematical Performance
| N | Decision Variables | Constraints | Native Status | Valid | Build Time | Solve Time | Total Time |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 3 | OPTIMAL | true | 0.002495 | 0.048945 | 0.052035 |
| 2 | 2 | 3 | INFEASIBLE | null | 0.000333 | 0.002287 | 0.002651 |
| 3 | 3 | 3 | INFEASIBLE | null | 0.000276 | 0.001942 | 0.002245 |
| 4 | 4 | 3 | OPTIMAL | true | 0.000243 | 0.001631 | 0.001912 |
| 8 | 8 | 3 | OPTIMAL | true | 0.000259 | 0.003803 | 0.004107 |
| 20 | 20 | 3 | OPTIMAL | true | 0.000377 | 0.012059 | 0.012495 |
| 50 | 50 | 3 | OPTIMAL | true | 0.000477 | 0.079264 | 0.079840 |
| 100 | 100 | 3 | OPTIMAL | true | 0.000681 | 0.433055 | 0.433894 |

*Note: "Decision Variables" refers to explicitly declared Model-level variables. CP-SAT internal solvers allocate additional Boolean/Integer structures dynamically which are not represented here.*

#### Preliminary SAT vs. CP-SAT Validation
*(Using historical SAT Pairwise measurements collected during the Prompt 09 audit).*

| N | Method | Status | Valid | Build/Encode Time | Solve Time | Total Time |
|---|---|---|---|---|---|---|
| 4 | SAT Pairwise | SAT | true | 0.000058 | 0.000070 | 0.000179 |
| 4 | CP-SAT | SAT | true | 0.000243 | 0.001631 | 0.001912 |
| 20 | SAT Pairwise | SAT | true | 0.002481 | 0.003398 | 0.007100 |
| 20 | CP-SAT | SAT | true | 0.000377 | 0.012059 | 0.012495 |
| 50 | SAT Pairwise | SAT | true | 0.022227 | 0.039854 | 0.082282 |
| 50 | CP-SAT | SAT | true | 0.000477 | 0.079264 | 0.079840 |
| 100 | SAT Pairwise | SAT | true | 0.317944 | 0.300608 | 0.777228 |
| 100 | CP-SAT | SAT | true | 0.000681 | 0.433055 | 0.433894 |

This initial comparison indicates OR-Tools API overhead slows it slightly for small problems, while SAT encoding dominates runtime sizes in larger instances due to $O(N^2)$ primary Boolean instantiation. This is purely indicative; formal benchmarks will assess true algorithm scaling behaviors.

### CLI 
Access the CP-SAT engine via the `cp_sat` solver module:

```bash
python -m src.cp_sat.solver --n 100 --time-limit 300 --workers 1 --random-seed 0 --json
python -m src.cp_sat.solver --n 8 --print-board
```

## Gurobi MIP Baseline

### Formulation
The Gurobi Mixed Integer Programming (MIP) solver uses a pure binary formulation similar to the SAT models, but enforces conditions using linear inequalities:
1. **Decision Variables**: $N^2$ binary variables $x_{i,j} \in \{0, 1\}$.
2. **Constraints**:
   - **Rows**: $\sum_{j} x_{i,j} = 1$ for each row $i$.
   - **Columns**: $\sum_{i} x_{i,j} = 1$ for each column $j$.
   - **Main Diagonals**: $\sum x_{i,j} \le 1$ for each main diagonal with length $\ge 2$.
   - **Anti-Diagonals**: $\sum x_{i,j} \le 1$ for each anti-diagonal with length $\ge 2$.
3. **Objective**: None (feasibility problem).

### Solver Configuration
- **Threads**: 1 (to ensure consistent deterministic search environments during evaluation).
- **Time limit**: 300.0 seconds.
- **Random seed**: 0.

### Status Mapping
The Gurobi solver's native statuses are mapped to the common project schemas:
- `OPTIMAL` $\rightarrow$ `SAT` (a valid solution is found).
- `INFEASIBLE` $\rightarrow$ `UNSAT` (proof that no solution exists).
- `TIME_LIMIT` $\rightarrow$ `TIMEOUT` (or `SAT` if a solution was found before the limit).
- `LICENSE_ERROR` $\rightarrow$ `LICENSE_ERROR` (gracefully caught size limit exception).
- Other statuses map to `UNKNOWN` or `ERROR`.

### License Constraints
The default `gurobipy` installation provides a restricted license limited to 2000 variables and 2000 constraints.
- N=20 requires 400 variables and 114 constraints (Supported).
- N=50 requires 2500 variables and 294 constraints (Exceeds variable limit $\rightarrow$ `LICENSE_ERROR`).
- N=100 requires 10000 variables and 594 constraints (Exceeds variable limit $\rightarrow$ `LICENSE_ERROR`).

To maintain a green CI pipeline, the framework catches the `"size-limited"` `gp.GurobiError` and returns a `LICENSE_ERROR` status instead of crashing. Tests verify this behavior for large N.

### Test Results
Tested on macOS with Python and Gurobi Optimizer.

Gurobi successfully found validated solutions (`SAT`) for $N=1, 4, 5, 8, 20$ and proved `UNSAT` for $N=2, 3$. The license constraint was gracefully captured for $N=50$ and $N=100$.

#### Preliminary Validation

| N | Status | Native Status | Valid | Binary Variables | Linear Constraints | Build Time | Solve Time |
|---|---|---|---|---|---|---|---|
| 4 | SAT | OPTIMAL | true | 16 | 18 | ~0.0003s | ~0.001s |
| 20 | SAT | OPTIMAL | true | 400 | 114 | ~0.002s | ~0.015s |
| 50 | LICENSE_ERROR | LICENSE_ERROR | null | null | null | null | null |
| 100 | LICENSE_ERROR | LICENSE_ERROR | null | null | null | null | null |

*Note: NOT FULLY VERIFIED FOR N=100 — LICENSE BLOCKER. Gurobi is expected to solve these sizes with a full license, but the pipeline handles the restricted license appropriately.*

### CLI 
Access the Gurobi engine via the `gurobi` solver module:

```bash
python -m src.gurobi.solver --n 20 --time-limit 300 --threads 1 --random-seed 0 --json
python -m src.gurobi.solver --n 8 --print-board
```

## IBM CPLEX MIP Baseline

### Formulation
The IBM ILOG CPLEX Mixed Integer Programming (MIP) solver baseline utilizes a binary MIP formulation identical to the Gurobi model:
1. **Decision Variables**: $N^2$ binary variables $x_{i,j} \in \{0, 1\}$.
2. **Constraints**:
   - **Rows**: $\sum_{j} x_{i,j} = 1$ for each row $i$.
   - **Columns**: $\sum_{i} x_{i,j} = 1$ for each column $j$.
   - **Main Diagonals**: $\sum x_{i,j} \le 1$ for each main diagonal with length $\ge 2$.
   - **Anti-Diagonals**: $\sum x_{i,j} \le 1$ for each anti-diagonal with length $\ge 2$.
3. **Objective**: None (feasibility problem).

### Solver Configuration
- **Threads**: 1.
- **Time limit**: 300.0 seconds.
- **Random seed**: 0.

### Status Mapping
The DOcplex and CPLEX statuses are strictly mapped according to CPLEX error codes:
- `101 (MIP optimal)`, `102 (MIP optimal tolerance)` $\rightarrow$ `SAT` (a valid solution is found).
- `103 (MIP infeasible)` $\rightarrow$ `UNSAT` (proof that no solution exists).
- `107 (Time limit exceeded, integer solution)` $\rightarrow$ `SAT` or `TIMEOUT`.
- `108 (Time limit exceeded, no integer solution)` $\rightarrow$ `TIMEOUT`.
- `1016 (Community size limit)` $\rightarrow$ `LICENSE_ERROR`.

### Environment and License Limits
Python `docplex` provides the modeling API, while `cplex` provides the optimization engine. 
The standard CPLEX Community Edition applies a promotional size limit of 1000 variables and 1000 constraints.
- N=20: 400 variables, 114 constraints (Supported).
- N=31: 961 variables, 180 constraints (Supported limit).
- N=50: 2500 variables, 294 constraints (Exceeds variable limit $\rightarrow$ `CPLEX Error 1016`).
- N=100: 10000 variables, 594 constraints (Exceeds variable limit $\rightarrow$ `CPLEX Error 1016`).

The solver gracefully handles Error 1016 through `docplex.mp.utils.DOcplexLimitsExceeded` and maps it to `LICENSE_ERROR` rather than crashing the framework.

### Test Results
Tested on macOS with Python, DOcplex 2.32, CPLEX 22.2.

CPLEX successfully built the model correctly up to N=100 (10000 vars, 594 constraints) in structural tests. Actual solving succeeded for $N=1, 4, 5, 8, 20$, and proved `UNSAT` for $N=2, 3$. The license constraint was verified and handled for $N=50$ and $N=100$.

#### Preliminary Validation

| N | Status | Valid | Binary Variables | Constraints | Build Time | Solve Time |
|---|---|---|---|---|---|---|
| 4 | SAT | true | 16 | 18 | ~0.04s | ~0.02s |
| 20 | SAT | true | 400 | 114 | ~0.05s | ~0.10s |
| 50 | LICENSE_ERROR | null | null | null | null | null |
| 100 | LICENSE_ERROR | null | null | null | null | null |

*Note: CPLEX MIP N=100 Model successfully constructed. Actual optimization blocked by Community Edition size limit. Not fully verified for performance benchmarking without a full license.*

### CLI 
Access the CPLEX engine via the `cplex_mip` solver module:

```bash
python -m src.cplex_mip.solver --n 20 --time-limit 300 --threads 1 --random-seed 0 --json
python -m src.cplex_mip.solver --n 8 --print-board
```

## IBM CP Optimizer Baseline

### Formulation
The IBM CP Optimizer solver utilizes a Constraint Programming (CP) formulation which is distinct from the binary MIP formulation. This exactly maps the structure of N-Queens:
1. **Decision Variables**: $N$ integer decision variables `q[row]` representing the column index, with a domain of `[0, N-1]`.
2. **Constraints**:
   - `AllDifferent(q)`: Each queen must be in a distinct column.
   - `AllDifferent(q[row] - row)`: Each queen must be in a distinct main diagonal.
   - `AllDifferent(q[row] + row)`: Each queen must be in a distinct anti-diagonal.
3. **Objective**: None (feasibility problem).

This matches the formulation used by OR-Tools CP-SAT, ensuring a fair baseline comparison across different CP engines.

### Solver Configuration
- **Workers**: 1.
- **Time limit**: 300.0 seconds.
- **Random seed**: 0.

### Status Mapping
The CP Optimizer statuses from `get_solve_status()` and `get_stop_cause()` are strictly mapped:
- `Feasible`, `Optimal` $\rightarrow$ `SAT` (a valid solution is found).
- `Infeasible` $\rightarrow$ `UNSAT` (proof that no solution exists).
- `Unknown` with `TimeLimit` stop cause $\rightarrow$ `TIMEOUT`.
- `JobFailed` $\rightarrow$ `ERROR`.

### Environment and License Limits
The CP Optimizer engine acts completely differently from the CPLEX MIP engine regarding Community limits. Although CPLEX MIP artificially blocks N=50 because it exceeds 1,000 binary variables, the CP Optimizer seamlessly solves N=100 because the model is natively described using only 100 integer variables and 3 global constraints! 

The framework accurately detects if the `docplex.cp` engine is entirely missing (`MISSING_CP_ENGINE`), if architecture binaries are incompatible (`ENVIRONMENT_ERROR`), or if standard license constraints eventually arise (`LICENSE_ERROR`).

### Test Results
Tested on macOS with Python, DOcplex 2.32, CPLEX 22.2.

CP Optimizer successfully built and **actually solved** N=100 successfully, escaping the restrictive boundary that constrained the CPLEX MIP implementation!

#### Preliminary Validation

| N | Status | Valid | Integer Variables | Constraints | Build Time | Solve Time | Total Time |
|---|---|---|---|---|---|---|---|
| 4 | SAT | true | 4 | 3 | ~0.0003s | ~0.22s | ~0.22s |
| 20 | SAT | true | 20 | 3 | ~0.0004s | ~0.01s | ~0.01s |
| 50 | SAT | true | 50 | 3 | ~0.0006s | ~0.01s | ~0.01s |
| 100 | SAT | true | 100 | 3 | ~0.0010s | ~0.01s | ~0.01s |

*Note: Build time is practically zero since CP only initializes 3 global constraints. The solve times above are initial, informal measurements on Apple Silicon.*

### CLI 
Access the CP Optimizer engine via the `cplex_cp` solver module:

```bash
python -m src.cplex_cp.solver --n 100 --time-limit 300 --workers 1 --random-seed 0 --json
python -m src.cplex_cp.solver --n 8 --print-board
```

## MIP License Limit Verification

To precisely identify the actual limits of the Community / Size-limited licenses on the exact MIP environments for `nqueens-sat`, an automated runner probed the boundaries empirically. Both Gurobi MIP and CPLEX MIP utilized identical configurations (`Time limit: 300`, `Threads: 1`, `Seed: 0`).

### Gurobi MIP Results

| N | Variables | Constraints | Status | Valid | Solve Time | Total Time |
|---|---:|---:|---|---|---|---|
| 32 | 1024 | 186 | SAT | True | ~0.050s | ~0.076s |
| 40 | 1600 | 234 | SAT | True | ~0.013s | ~0.021s |
| 44 | 1936 | 258 | SAT | True | ~0.014s | ~0.023s |
| 45 | 2025 | 264 | LICENSE_ERROR | null | null | null |

**Conclusion for Gurobi MIP:**
- Largest tested N with SAT + Valid: **44**
- Largest tested N blocked by license: **45**
- License boundary confirmed: **YES** (The 2,000 variable threshold blocks $45^2 = 2025$ variables).

### CPLEX MIP Results

| N | Variables | Constraints | Status | Valid | Solve Time | Total Time |
|---|---:|---:|---|---|---|---|
| 25 | 625 | 144 | SAT | True | ~0.067s | ~0.127s |
| 30 | 900 | 174 | SAT | True | ~0.005s | ~0.021s |
| 31 | 961 | 180 | SAT | True | ~0.005s | ~0.021s |
| 32 | 1024 | 186 | LICENSE_ERROR | null | null | null |

**Conclusion for CPLEX MIP:**
- Largest tested N with SAT + Valid: **31**
- Largest tested N blocked by license: **32**
- License boundary confirmed: **YES** (The 1,000 variable threshold blocks $32^2 = 1024$ variables).

Raw and processed outputs from this supplementary check are saved at:
- `results/raw/mip_license_limits.json`
- `results/processed/mip_license_limits.csv`

## Reproducible Benchmark Framework

This project includes a fully automated, deterministic, and fair benchmarking framework for comparing the performance of 9 N-Queens solvers:

1. **SAT Pairwise** (Glucose3)
2. **SAT Binary** (Glucose3)
3. **SAT Sequential** (Glucose3)
4. **SAT Commander** (Glucose3)
5. **SAT Product** (Glucose3)
6. **CP-SAT** (OR-Tools)
7. **Gurobi MIP**
8. **CPLEX MIP**
9. **CPLEX CP** (IBM CP Optimizer)

### Research Goal
To provide a reproducible empirical evaluation of different constraint encodings and solver technologies (SAT, MIP, CP) on the exact same problem formulations, maintaining strict fairness in hardware, limits, and configurations.

### Hardware/Software Environment
- Executed via `experiments.benchmark_runner`
- Single worker/thread enforced across all solvers
- Detailed system and package metadata collected automatically (`results/metadata/`)

### Solver Configurations
- **Workers/Threads**: 1
- **Random Seed**: 0 (where supported)
- **Time limit (internal)**: 300 seconds
- **Subprocess timeout (external)**: 330 seconds
- **Memory isolation**: Each solver execution runs in a fresh, isolated subprocess.

### SAT Phase Policy
**CRITICAL NOTE**: While earlier explorations used a legacy encoding-specific phase override for the `Product` encoding (which artificially guided it to a solution), the **primary benchmark uses `solver_default` for all SAT encodings**. This ensures algorithmic fairness. As a result, the Product encoding's benchmark performance may differ substantially from historical Prompt 09 results.

### Benchmark Configurations
We provide standard schedules (N values and repetitions):
- `smoke`: N = [4, 8], 1 repetition. Used for quick checks.
- `pilot`: N = [4, 8, 16, 20, 31, 32, 44, 50, 64, 100], 1 repetition.
- `full`: N = [4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100], 5 repetitions.

A fixed random seed (`2026`) is used to deterministically shuffle the execution order of solvers within each (N, repetition) block to avoid systemic sequence bias.

### Warm-up Policy
Before running the measured trials, a single unrecorded warm-up trial (N=4) is executed for each method to reduce the impact of cold-starts (e.g. OS caching, Python interpreter startup).

### License Handling
Gurobi and CPLEX MIP solvers are subject to community license limits (2,000 and 1,000 variables/constraints, respectively). The benchmark runner proactively blocks `N >= 45` for Gurobi and `N >= 32` for CPLEX MIP with a `BLOCKED_LICENSE` status to save time and clearly reflect environment constraints. 

### Output Data Schema
Raw records are appended atomically as JSONL (`results/raw/`). 
Each trial includes:
- **Metrics**: `pipeline_total_time`, `process_wall_time`, solver-specific phases (e.g., `encoding_time`, `build_time`, `solve_time`).
- **Validation**: Independent programmatic validation of output positions.

CSV exports (`results/processed/`) are automatically generated, including aggregated statistical summaries (Mean, Median, Standard Deviation, Success Rates). Note that `mean/median_time` only compute across successful (SAT+Valid) runs. Failed runs (Timeout, License Blocked, Error) are excluded from time averages.

### How to Run

1. **Smoke Test**
```bash
python -m experiments.benchmark_runner --mode smoke
```

2. **Pilot Run**
```bash
python -m experiments.benchmark_runner --mode pilot
```

3. **Full Official Benchmark**
```bash
python -m experiments.benchmark_runner --mode full
```

*To resume an interrupted run, simply add the `--resume` flag. The framework will pick up where it left off!*

### Limitations & Threats to Validity
- **Process Startup Overhead**: Since every trial spawns a new Python subprocess, `process_wall_time` will include interpreter initialization. We rely primarily on internal `pipeline_total_time` for solver analysis.
- **Environment Variance**: CP Optimizer limits and MIP license limits depend on local installation status. (If CP Optimizer binary is inaccessible in your PATH/sandbox, it fails gracefully with `MISSING_CP_ENGINE`).
- **Product Policy Change**: As mentioned, enforcing `solver_default` means Product will likely perform worse than its tuned counterpart.

### Benchmark Execution Status (Prompt 15.1)

#### 1. CPLEX CP Subprocess Error & Diagnosis
During initial testing, the IBM CP Optimizer (`cplex_cp`) solver consistently failed with a `MISSING_CP_ENGINE` error when invoked through the benchmark framework's `subprocess.run`, despite working when run directly from the CLI.
**Root cause**: DOcplex CP relies on discovering the `cpoptimizer` executable via the system `PATH`. When launched within Python's `subprocess.run()`, the virtual environment's `bin/` directory (`.venv/bin`) was not automatically propagated into the `PATH` of the subprocess, rendering the executable invisible to the solver agent.
**Fix Implemented**: Modified `experiments/benchmark_runner.py` to explicitly inject `str(Path(".venv/bin").absolute())` into the `PATH` of the subprocess environment before execution.

#### 2. Environment Configuration
- Operating System: macOS
- CPU/Architecture: System default (Apple Silicon / Intel compatible)
- Python Version: 3.13.x
- Solver Versions: CPLEX MIP & CP Optimizer (22.2.0.1 via pip), Gurobi, OR-Tools, and PySAT confirmed accessible within `.venv`.

#### 3. Pilot Results & Full Configuration
**Pilot Run**: Completed N=4 to N=100 for all 9 methods (1 rep). The CPLEX CP subprocess successfully executed without errors. Expected timeouts were observed (e.g., `sat_product` at larger N values due to `solver_default` phase policy).

**Full Benchmark Configuration**:
- **N Values**: `[4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100]`
- **Repetitions**: 5
- **Timeout**: 300s internal / 330s external
- **SAT Phase Policy**: `solver_default`
- **Workers/Threads**: 1
- **Random/Schedule Seed**: `0` / `2026`

#### 4. Execution Counts
*Note: The Full Benchmark is currently running in the background and its dataset is PARTIAL. The counts below reflect the planned structure.*
- **Planned records**: 495
- **Completed records**: [Running in background]
- **Successful/Timeout/Blocked/Error**: [Pending completion of full dataset]
- **Estimated License Blocked**: 45 runs total across Gurobi MIP (N>=45) and CPLEX MIP (N>=32).

#### 5. Output Files & Artifacts
The framework incrementally saves data to prevent loss:
- `results/raw/benchmark_nqueens_primary_full.jsonl`
- `results/processed/benchmark_nqueens_primary_full.csv`
- `results/processed/benchmark_summary_nqueens_primary_full.csv`
- `results/metadata/benchmark_nqueens_primary_full_metadata.json`

*(Previous pilot iterations are safely archived as `benchmark_pilot_initial`)*

#### 6. Resuming the Benchmark
If the `run_all.sh` background script is interrupted, the benchmark can be resumed safely without duplicating records:
```bash
python -m experiments.benchmark_runner --mode full --resume
```

#### 7. Remaining Limitations
- `sat_product` evaluates very slowly under `solver_default` compared to its tailored legacy heuristic. Timeouts are recorded accurately as `TIMEOUT`.
- The reported `process_wall_time` inherently includes interpreter start-up overhead. The core metric `pipeline_total_time` should be used for solver comparisons.
- Statistical significance requires completion of the Full dataset (5 reps per N per method).
