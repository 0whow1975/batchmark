"""Tests for batchmark.compare module."""

import pytest
from batchmark.runner import BenchmarkResult
from batchmark.compare import compare_results, render_comparison_table, ComparisonRow


def make_result(size: int, elapsed: float, exit_code: int = 0) -> BenchmarkResult:
    return BenchmarkResult(
        command="echo test",
        input_size=size,
        runs=1,
        elapsed=elapsed,
        exit_code=exit_code,
        timed_out=False,
    )


def test_compare_results_basic():
    groups = {
        "cmd_a": [make_result(100, 1.0), make_result(200, 2.0)],
        "cmd_b": [make_result(100, 2.0), make_result(200, 3.0)],
    }
    result = compare_results(groups)
    assert set(result.keys()) == {100, 200}

    rows_100 = result[100]
    assert len(rows_100) == 2
    assert rows_100[0].label == "cmd_a"
    assert rows_100[0].relative == pytest.approx(1.0)
    assert rows_100[1].label == "cmd_b"
    assert rows_100[1].relative == pytest.approx(2.0)


def test_compare_results_empty():
    assert compare_results({}) == {}


def test_compare_results_skips_failures():
    groups = {
        "cmd_a": [make_result(100, 1.0)],
        "cmd_b": [make_result(100, 0.5, exit_code=1)],  # failed run
    }
    result = compare_results(groups)
    rows = result[100]
    labels = [r.label for r in rows]
    assert "cmd_b" not in labels
    assert "cmd_a" in labels


def test_compare_results_relative_normalized():
    groups = {
        "fast": [make_result(50, 0.5)],
        "slow": [make_result(50, 1.5)],
    }
    result = compare_results(groups)
    rows = result[50]
    assert rows[0].relative == pytest.approx(1.0)
    assert rows[1].relative == pytest.approx(3.0)


def test_render_comparison_table_contains_labels():
    groups = {
        "alpha": [make_result(10, 0.1)],
        "beta": [make_result(10, 0.3)],
    }
    comparison = compare_results(groups)
    table = render_comparison_table(comparison)
    assert "alpha" in table
    assert "beta" in table
    assert "Size" in table
    assert "Rel" in table
    assert "1.00x" in table
