"""Tests for batchmark.scaling."""
import math
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.scaling import (
    ScalingResult,
    analyze_scaling,
    render_scaling_table,
    _fit_models,
)


def make_result(cmd, size, mean, success=True):
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=[mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        success=success,
        exit_code=0 if success else 1,
    )


def test_fit_models_linear():
    # Perfect O(n) data: y = 2*n
    sizes = [10.0, 20.0, 30.0, 40.0, 50.0]
    times = [2 * s for s in sizes]
    models = _fit_models(sizes, times)
    assert models["O(n)"] > 0.99
    assert models["O(n)"] >= models["O(n^2)"]


def test_fit_models_quadratic():
    # Perfect O(n^2) data: y = n^2
    sizes = [10.0, 20.0, 30.0, 40.0, 50.0]
    times = [s ** 2 for s in sizes]
    models = _fit_models(sizes, times)
    assert models["O(n^2)"] > 0.99


def test_analyze_scaling_basic():
    results = [
        make_result("sort", 100, 0.10),
        make_result("sort", 200, 0.20),
        make_result("sort", 300, 0.30),
        make_result("sort", 400, 0.40),
    ]
    scaling = analyze_scaling(results)
    assert len(scaling) == 1
    assert scaling[0].command == "sort"
    assert scaling[0].best_fit == "O(n)"
    assert scaling[0].r_squared > 0.99


def test_analyze_scaling_skips_failures():
    results = [
        make_result("cmd", 100, 0.1, success=False),
        make_result("cmd", 200, 0.2, success=False),
        make_result("cmd", 300, 0.3, success=False),
    ]
    scaling = analyze_scaling(results)
    assert scaling == []


def test_analyze_scaling_too_few_points():
    results = [
        make_result("cmd", 100, 0.1),
        make_result("cmd", 200, 0.2),
    ]
    scaling = analyze_scaling(results)
    assert scaling == []


def test_analyze_scaling_command_filter():
    results = [
        make_result("grep", 100, 0.1),
        make_result("grep", 200, 0.2),
        make_result("grep", 300, 0.3),
        make_result("awk", 100, 0.05),
        make_result("awk", 200, 0.10),
        make_result("awk", 300, 0.15),
    ]
    scaling = analyze_scaling(results, command="grep")
    assert len(scaling) == 1
    assert scaling[0].command == "grep"


def test_render_scaling_table_empty():
    output = render_scaling_table([])
    assert "No scaling" in output


def test_render_scaling_table_basic():
    rows = [
        ScalingResult(
            command="sort",
            best_fit="O(n)",
            r_squared=0.9987,
            coefficients={"O(n)": 0.9987, "O(n^2)": 0.85},
        )
    ]
    table = render_scaling_table(rows)
    assert "sort" in table
    assert "O(n)" in table
    assert "0.9987" in table
