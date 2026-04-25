"""Tests for batchmark.efficiency."""
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.efficiency import compute_efficiency, render_efficiency_table


def make_result(command, size, mean, success=True):
    r = BenchmarkResult(command=command, size=size, times=[mean])
    r.success = success
    r.mean = mean if success else None
    r.median = mean if success else None
    r.stdev = 0.0 if success else None
    r.min = mean if success else None
    r.max = mean if success else None
    return r


def test_compute_efficiency_basic():
    results = [
        make_result("cmd_a", 100, 2.0),
        make_result("cmd_a", 200, 2.0),
    ]
    rows = compute_efficiency(results)
    assert len(rows) == 2
    # size=200, time=2.0 => efficiency=100; size=100, time=2.0 => efficiency=50
    assert rows[0].efficiency == pytest.approx(100.0)
    assert rows[0].size == 200
    assert rows[1].efficiency == pytest.approx(50.0)
    assert rows[1].size == 100


def test_compute_efficiency_rank_order():
    results = [
        make_result("cmd", 1000, 1.0),
        make_result("cmd", 500, 1.0),
        make_result("cmd", 100, 1.0),
    ]
    rows = compute_efficiency(results)
    ranks = [r.rank for r in rows]
    assert ranks == [1, 2, 3]
    assert rows[0].efficiency == pytest.approx(1000.0)


def test_compute_efficiency_skips_failures():
    results = [
        make_result("cmd", 100, 2.0, success=False),
        make_result("cmd", 200, 4.0),
    ]
    rows = compute_efficiency(results)
    valid = [r for r in rows if r.efficiency is not None]
    invalid = [r for r in rows if r.efficiency is None]
    assert len(valid) == 1
    assert len(invalid) == 1
    assert valid[0].rank == 1
    assert invalid[0].rank == 2


def test_compute_efficiency_command_filter():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_b", 100, 1.0),
    ]
    rows = compute_efficiency(results, command="cmd_a")
    assert all(r.command == "cmd_a" for r in rows)
    assert len(rows) == 1


def test_compute_efficiency_zero_time():
    results = [make_result("cmd", 100, 0.0)]
    rows = compute_efficiency(results)
    assert rows[0].efficiency is None


def test_render_efficiency_table_empty():
    output = render_efficiency_table([])
    assert "No efficiency data" in output


def test_render_efficiency_table_basic():
    results = [make_result("fast_cmd", 1000, 2.0)]
    rows = compute_efficiency(results)
    table = render_efficiency_table(rows)
    assert "fast_cmd" in table
    assert "1000" in table
    assert "500.0000" in table


def test_render_efficiency_table_failure_row():
    results = [make_result("bad_cmd", 100, 1.0, success=False)]
    rows = compute_efficiency(results)
    table = render_efficiency_table(rows)
    assert "N/A" in table
    assert "bad_cmd" in table
