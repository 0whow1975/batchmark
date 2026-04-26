"""Tests for batchmark.elbow."""
import pytest
from batchmark.elbow import detect_elbows, render_elbow_table, ElbowResult
from batchmark.runner import BenchmarkResult


def make_result(cmd: str, size: int, times, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=list(times),
        success=success,
        error=None,
    )


def test_detect_elbows_basic():
    # Flat growth then sharp jump -> elbow at size 30
    results = [
        make_result("cmd", 10, [0.1, 0.1]),
        make_result("cmd", 20, [0.2, 0.2]),
        make_result("cmd", 30, [0.3, 0.3]),
        make_result("cmd", 40, [1.5, 1.5]),
        make_result("cmd", 50, [3.0, 3.0]),
    ]
    rows = detect_elbows(results)
    assert len(rows) == 1
    r = rows[0]
    assert r.command == "cmd"
    assert r.elbow_size is not None
    # The sharpest curvature should be around the inflection point
    assert r.elbow_size in [30, 40]


def test_detect_elbows_too_few_points():
    results = [
        make_result("cmd", 10, [0.1]),
        make_result("cmd", 20, [0.2]),
    ]
    rows = detect_elbows(results)
    assert len(rows) == 1
    assert rows[0].elbow_size is None
    assert rows[0].sizes == []


def test_detect_elbows_skips_failures():
    results = [
        make_result("cmd", 10, [0.1]),
        make_result("cmd", 20, [], success=False),
        make_result("cmd", 30, [0.3]),
    ]
    rows = detect_elbows(results)
    # Only 2 valid points -> no elbow
    assert rows[0].elbow_size is None


def test_detect_elbows_multiple_commands():
    results = [
        make_result("a", 10, [0.1]),
        make_result("a", 20, [0.2]),
        make_result("a", 30, [0.4]),
        make_result("a", 40, [2.0]),
        make_result("a", 50, [4.0]),
        make_result("b", 10, [1.0]),
        make_result("b", 20, [2.0]),
        make_result("b", 30, [3.0]),
        make_result("b", 40, [4.0]),
        make_result("b", 50, [5.0]),
    ]
    rows = detect_elbows(results)
    cmds = [r.command for r in rows]
    assert "a" in cmds
    assert "b" in cmds


def test_render_elbow_table_contains_command():
    rows = [
        ElbowResult("mycmd", 40, 1.2345, 3, [10, 20, 30, 40, 50], [0.1, 0.2, 0.3, 1.2, 2.0])
    ]
    table = render_elbow_table(rows)
    assert "mycmd" in table
    assert "40" in table
    assert "1.2345" in table


def test_render_elbow_table_no_elbow():
    rows = [ElbowResult("cmd", None, None, None, [], [])]
    table = render_elbow_table(rows)
    assert "n/a" in table
    assert "cmd" in table
