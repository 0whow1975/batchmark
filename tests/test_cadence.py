"""Tests for batchmark.cadence."""

from __future__ import annotations

from batchmark.runner import BenchmarkResult
from batchmark.cadence import analyze_cadence, render_cadence_table, _label


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


def test_label_steady():
    assert _label(0.05) == "steady"


def test_label_irregular():
    assert _label(0.20) == "irregular"


def test_label_erratic():
    assert _label(0.50) == "erratic"


def test_analyze_cadence_basic():
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 2.0),
        make_result("cmd", 400, 4.0),
    ]
    rows = analyze_cadence(results)
    assert len(rows) == 1
    r = rows[0]
    assert r.command == "cmd"
    assert len(r.ratios) == 2
    assert abs(r.ratios[0] - 2.0) < 1e-9
    assert abs(r.ratios[1] - 2.0) < 1e-9
    assert r.cv < 1e-9          # perfectly steady
    assert r.label == "steady"


def test_analyze_cadence_skips_failures():
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 2.0, success=False),
        make_result("cmd", 400, 4.0),
    ]
    rows = analyze_cadence(results)
    # only two successful sizes -> one ratio
    assert len(rows) == 1
    assert len(rows[0].ratios) == 1


def test_analyze_cadence_too_few_sizes():
    results = [make_result("cmd", 100, 1.0)]
    rows = analyze_cadence(results)
    assert rows == []


def test_analyze_cadence_command_filter():
    results = [
        make_result("a", 100, 1.0),
        make_result("a", 200, 2.0),
        make_result("b", 100, 1.0),
        make_result("b", 200, 3.0),
    ]
    rows = analyze_cadence(results, command="a")
    assert len(rows) == 1
    assert rows[0].command == "a"


def test_analyze_cadence_multiple_commands_sorted():
    results = [
        make_result("z", 100, 1.0),
        make_result("z", 200, 2.0),
        make_result("a", 100, 1.0),
        make_result("a", 200, 2.0),
    ]
    rows = analyze_cadence(results)
    assert [r.command for r in rows] == ["a", "z"]


def test_render_cadence_table_empty():
    assert "No cadence" in render_cadence_table([])


def test_render_cadence_table_contains_command():
    results = [
        make_result("mycommand", 100, 1.0),
        make_result("mycommand", 200, 2.0),
    ]
    rows = analyze_cadence(results)
    table = render_cadence_table(rows)
    assert "mycommand" in table
    assert "steady" in table
