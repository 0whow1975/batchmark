"""Extra rendering tests for batchmark.cadence."""

from __future__ import annotations

from batchmark.runner import BenchmarkResult
from batchmark.cadence import analyze_cadence, render_cadence_table


def make_result(cmd: str, size: int, mean: float, success: bool = True) -> BenchmarkResult:
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
    )


def test_render_table_contains_header():
    results = [make_result("cmd", 100, 1.0), make_result("cmd", 200, 2.0)]
    table = render_cadence_table(analyze_cadence(results))
    assert "Command" in table
    assert "CV" in table
    assert "Label" in table


def test_render_table_step_count():
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 2.0),
        make_result("cmd", 400, 4.0),
        make_result("cmd", 800, 8.0),
    ]
    rows = analyze_cadence(results)
    table = render_cadence_table(rows)
    # 3 ratios for 4 sizes
    assert "3" in table


def test_render_erratic_label_present():
    # Highly variable ratios -> erratic
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 10.0),
        make_result("cmd", 400, 2.0),
        make_result("cmd", 800, 50.0),
    ]
    rows = analyze_cadence(results)
    table = render_cadence_table(rows)
    assert "erratic" in table or "irregular" in table


def test_render_mean_ratio_nonzero():
    results = [make_result("cmd", 100, 1.0), make_result("cmd", 200, 3.0)]
    rows = analyze_cadence(results)
    assert abs(rows[0].mean_ratio - 3.0) < 1e-9
    table = render_cadence_table(rows)
    assert "3.0000" in table
