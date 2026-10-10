import pytest
from experiments.visualization.plot_config import (
    METHOD_COLORS,
    METHOD_MARKERS,
    METHOD_LABELS,
    SAT_METHODS,
    EXACT_METHODS,
)
from experiments.solver_registry import METHODS

def test_cp_sat_identifier():
    assert "cp_sat" in METHOD_COLORS
    assert "cp_sat" in METHOD_MARKERS
    assert "cp_sat" in METHOD_LABELS
    assert "or_tools_cp_sat" not in METHOD_COLORS
    assert "or_tools_cp_sat" not in METHOD_MARKERS
    assert "or_tools_cp_sat" not in METHOD_LABELS

def test_all_methods_mapped():
    for method in METHODS:
        assert method in METHOD_COLORS, f"Missing color for {method}"
        assert method in METHOD_MARKERS, f"Missing marker for {method}"
        assert method in METHOD_LABELS, f"Missing label for {method}"

def test_no_extra_methods():
    for method in METHOD_COLORS:
        assert method in METHODS, f"Unexpected method {method} in COLORS"
    for method in METHOD_MARKERS:
        assert method in METHODS, f"Unexpected method {method} in MARKERS"
    for method in METHOD_LABELS:
        assert method in METHODS, f"Unexpected method {method} in LABELS"
