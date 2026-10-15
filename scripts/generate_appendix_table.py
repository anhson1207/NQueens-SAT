#!/usr/bin/env python3
"""
generate_appendix_table.py

Automated script to verify and generate Table 9 in report/paper/sections/09_appendix.tex.
Separates sources of data:
- Formula: computed from closed-form algebraic expressions.
- Generated: exact clause count from CNF generator (for N <= 100) or empirical logs.
- Pairwise at N=200 was blocked preflight by NOT_RUN_RESOURCE_POLICY and is recorded as '---'.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.sat.encodings.pairwise import encode_nqueens_pairwise
from src.sat.encodings.sequential import encode_nqueens_sequential

def c_pairwise(n: int) -> int:
    return 2 * n + n * n * (n - 1) + n * (n - 1) * (2 * n - 1) // 3

def c_sequential(n: int) -> int:
    return 12 * n * n - 22 * n + 12

def a_sequential(n: int) -> int:
    return 4 * n * n - 6 * n + 2

def build_table_rows(instance_sizes: list[int]) -> list[dict]:
    # Load primary benchmark raw logs for empirical verification
    raw_log_path = ROOT / "results" / "raw" / "benchmark_nqueens_primary_full.jsonl"
    raw_clauses = {}
    if raw_log_path.exists():
        with open(raw_log_path, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                raw_clauses[(r["method_id"], r["n"])] = r.get("clauses")

    rows = []
    for n in instance_sizes:
        pw_formula = c_pairwise(n)
        seq_formula = c_sequential(n)

        # Pairwise generator: only up to N=100 to avoid multi-GB memory allocation at N=200
        if n <= 100:
            pw_gen_clauses = len(encode_nqueens_pairwise(n))
            # Verify consistency with raw benchmark log if available
            log_val = raw_clauses.get(("sat_pairwise", n))
            if log_val is not None:
                assert pw_gen_clauses == log_val, f"Raw log mismatch for Pairwise N={n}"
            pw_gen_str = f"{pw_gen_clauses:,}"
        else:
            # Pairwise was NOT run at N=200 due to preflight memory cap
            pw_gen_str = "---"

        # Sequential generator: safe to generate even at N=200
        seq_clauses, total_vars = encode_nqueens_sequential(n)
        seq_gen_count = len(seq_clauses)
        seq_aux_count = total_vars - n * n
        assert seq_aux_count == a_sequential(n), f"Aux variable mismatch for Sequential N={n}"

        log_val = raw_clauses.get(("sat_sequential", n))
        if log_val is not None:
            assert seq_gen_count == log_val, f"Raw log mismatch for Sequential N={n}"

        rows.append({
            "n": n,
            "pw_formula": f"{pw_formula:,}",
            "pw_generated": pw_gen_str,
            "seq_formula": f"{seq_formula:,}",
            "seq_generated": f"{seq_gen_count:,}",
        })
    return rows

def format_latex_table(rows: list[dict]) -> str:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Exact theoretical vs.\ generated structural counts across instance sizes.}",
        r"\label{tab:appendix_verification}",
        r"\begin{tabular}{rrrrr}",
        r"\toprule",
        r"$N$ & $C_{\text{pairwise}}$ (Formula) & $C_{\text{pairwise}}$ (Generated) & $C_{\text{sequential}}$ (Formula) & $C_{\text{sequential}}$ (Generated) \\",
        r"\midrule",
    ]
    for r in rows:
        lines.append(f"{r['n']:<4} & {r['pw_formula']:<14} & {r['pw_generated']:<14} & {r['seq_formula']:<14} & {r['seq_generated']:<14} \\\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\vspace{1ex}",
        r"\begin{minipage}{\linewidth}",
        r"\footnotesize \textit{Note:} For Pairwise at $N=200$, the model generates $13,253,800$ clauses by closed-form derivation. However, because the preflight memory guard policy proactively blocked execution (\texttt{NOT\_RUN\_RESOURCE\_POLICY}) to avoid exceeding system memory limits, no CNF clause instance was materialized in memory during benchmarking (indicated by ``---'').",
        r"\end{minipage}",
        r"\end{table}",
    ])
    return "\n".join(lines)

def main():
    sizes = [4, 8, 16, 20, 31, 32, 40, 44, 50, 64, 100, 200]
    rows = build_table_rows(sizes)
    table_latex = format_latex_table(rows)
    print(table_latex)

if __name__ == "__main__":
    main()
