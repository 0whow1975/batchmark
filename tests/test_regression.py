import pytest
from batchmark.runner import BenchmarkResult
from batchmark.regression import detect_regressions, render_regression_table, RegressionResult


def make_result(command, size, times, exit_code=0):
    return BenchmarkResult(command=command, size=size, times=times, exit_code=exit_code)


def test_detect_regressions_basic():
    baseline = [make_result("cmd", 100, [1.0, 1.0, 1.0])]
    current = [make_result("cmd", 100, [1.2, 1.2, 1.2])]
    rows = detect_regressions(baseline, current, threshold=0.10)
    assert len(rows) == 1
    assert rows[0].is_regression is True
    assert abs(rows[0].pct_change - 0.2) < 1e-6


def test_detect_regressions_no_regression():
    baseline = [make_result("cmd", 100, [1.0, 1.0])]
    current = [make_result("cmd", 100, [1.05, 1.05])]
    rows = detect_regressions(baseline, current, threshold=0.10)
    assert len(rows) == 1
    assert rows[0].is_regression is False


def test_detect_regressions_skips_failures():
    baseline = [make_result("cmd", 100, [], exit_code=1)]
    current = [make_result("cmd", 100, [2.0])]
    rows = detect_regressions(baseline, current)
    assert rows == []


def test_detect_regressions_no_match():
    baseline = [make_result("other", 100, [1.0])]
    current = [make_result("cmd", 100, [1.5])]
    rows = detect_regressions(baseline, current)
    assert rows == []


def test_detect_regressions_multiple():
    baseline = [
        make_result("cmd", 100, [1.0]),
        make_result("cmd", 200, [2.0]),
    ]
    current = [
        make_result("cmd", 100, [1.5]),
        make_result("cmd", 200, [2.1]),
    ]
    rows = detect_regressions(baseline, current, threshold=0.10)
    assert len(rows) == 2
    assert rows[0].is_regression is True
    assert rows[1].is_regression is False


def test_render_regression_table_empty():
    out = render_regression_table([])
    assert "No comparable" in out


def test_render_regression_table_basic():
    baseline = [make_result("cmd", 100, [1.0])]
    current = [make_result("cmd", 100, [1.2])]
    rows = detect_regressions(baseline, current)
    out = render_regression_table(rows)
    assert "cmd" in out
    assert "REGR" in out
