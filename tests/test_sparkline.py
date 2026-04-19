import pytest
from batchmark.sparkline import make_sparkline, sparklines_for_results, render_sparkline_table, SPARK_CHARS
from batchmark.runner import BenchmarkResult


def make_result(cmd, size, mean, success=True):
    return BenchmarkResult(
        command=cmd, size=size, times=[mean],
        mean=mean, median=mean, stdev=0.0,
        min=mean, max=mean, success=success, exit_code=0
    )


def test_make_sparkline_empty():
    assert make_sparkline([]) == ""


def test_make_sparkline_single():
    s = make_sparkline([1.0])
    assert len(s) == 1
    assert s == SPARK_CHARS[4]


def test_make_sparkline_ascending():
    s = make_sparkline([1.0, 2.0, 3.0, 4.0])
    assert len(s) == 4
    # first char should be lower than last
    assert SPARK_CHARS.index(s[0]) < SPARK_CHARS.index(s[-1])


def test_make_sparkline_flat():
    s = make_sparkline([5.0, 5.0, 5.0])
    assert len(s) == 3
    assert all(c == s[0] for c in s)


def test_sparklines_for_results_basic():
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 3.0),
    ]
    out = sparklines_for_results(results)
    assert "cmd" in out
    assert len(out["cmd"]) == 3


def test_sparklines_skips_failures():
    results = [
        make_result("cmd", 10, 1.0, success=False),
        make_result("cmd", 20, 2.0),
    ]
    out = sparklines_for_results(results)
    assert len(out["cmd"]) == 1


def test_sparklines_empty():
    assert sparklines_for_results([]) == {}


def test_render_sparkline_table_basic():
    results = [
        make_result("grep", 100, 0.5),
        make_result("grep", 200, 1.0),
        make_result("awk", 100, 0.3),
        make_result("awk", 200, 0.9),
    ]
    table = render_sparkline_table(results)
    assert "grep" in table
    assert "awk" in table
    assert "Trend" in table


def test_render_sparkline_table_no_data():
    assert render_sparkline_table([]) == "No data."
