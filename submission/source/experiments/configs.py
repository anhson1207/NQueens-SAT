"""Shared constants for SAT integration checks (not formal benchmarks)."""

SAT_ENCODINGS = (
    "pairwise",
    "binary",
    "sequential",
    "commander",
    "product",
)

PHASE_POLICIES = ("solver_default", "aux_false", "legacy")
DEFAULT_PHASE_POLICY = "legacy"
SAT_TIMEOUT_SECONDS = 300

CORRECTNESS_N_VALUES = (1, 2, 3, 4, 5, 8)
EXPECTED_STATUS = {
    1: "SAT",
    2: "UNSAT",
    3: "UNSAT",
    4: "SAT",
    5: "SAT",
    8: "SAT",
    20: "SAT",
    50: "SAT",
    100: "SAT",
}

EXPECTED_STRUCTURE = {
    (4, "pairwise"): (16, 0, 16, 84),
    (4, "binary"): (16, 32, 48, 120),
    (4, "sequential"): (16, 42, 58, 116),
    (4, "commander"): (16, 20, 36, 104),
    (4, "product"): (16, 68, 84, 160),
    (100, "pairwise"): (10_000, 0, 10_000, 1_646_900),
    (100, "binary"): (10_000, 3_678, 13_678, 269_024),
    (100, "sequential"): (10_000, 39_402, 49_402, 117_812),
    (100, "commander"): (10_000, 20_536, 30_536, 118_092),
    (100, "product"): (10_000, 9_492, 19_492, 116_672),
}

REQUIRED_RESULT_FIELDS = frozenset(
    {
        "method",
        "solver",
        "encoding",
        "n",
        "status",
        "has_solution",
        "valid",
        "positions",
        "primary_variables",
        "auxiliary_variables",
        "total_variables",
        "clauses",
        "phase_policy",
        "phase_override",
        "phase_literals",
        "encoding_time",
        "load_time",
        "configuration_time",
        "search_time",
        "solve_time",
        "decode_validate_time",
        "total_time",
        "statistics",
        "error",
    }
)

REQUIRED_GLUCOSE3_STATISTICS = frozenset(
    {"restarts", "conflicts", "decisions", "propagations"}
)

ENCODING_VARIANTS = {
    "pairwise": "Pairwise/Binomial",
    "binary": "Binary/Bitwise",
    "sequential": "Sinz Sequential Counter",
    "commander": "Recursive Commander (group_size=3)",
    "product": "Non-recursive 2-Product with Pairwise auxiliary AMO",
}
