"""Tests for batchmark.winrate."""
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.winrate import compute_win_rates, render_winrate_table, WinRateRow


def make_result(command, size, mean_time, success=True):
    return BenchmarkResult(
        command=command,
        size=size,
        times=[mean_time],
        mean_time=mean_time,
        median_time=mean_time,
        stdev_time=0.0,
        min_time=mean_time,
        max_time=mean_time,
        success=success,
        error=None,
    )


def test_compute_win_rates_basic():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_a", 200, 3.0),
        make_result("cmd_b", 200, 2.5),
    ]
    rows = compute_win_rates(results)
    assert len(rows) == 1
    row = rows[0]
    assert row.command_a == "cmd_a"
    assert row.command_b == "cmd_b"
    assert row.wins_a == 1  # size 100
    assert row.wins_b == 1  # size 200
    assert row.ties == 0
    assert row.total == 2


def test_compute_win_rates_skips_failures():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_b", 100, 2.0, success=False),
    ]
    rows = compute_win_rates(results)
    # Only one command has valid data, no pairs
    assert rows == []


def test_compute_win_rates_tie():
    results = [
        make_result("cmd_a", 100, 1.5),
        make_result("cmd_b", 100, 1.5),
    ]
    rows = compute_win_rates(results)
    assert len(rows) == 1
    assert rows[0].ties == 1
    assert rows[0].wins_a == 0
    assert rows[0].wins_b == 0


def test_compute_win_rates_three_commands():
    results = [
        make_result("a", 10, 1.0),
        make_result("b", 10, 2.0),
        make_result("c", 10, 3.0),
    ]
    rows = compute_win_rates(results)
    assert len(rows) == 3  # (a,b), (a,c), (b,c)


def test_win_rate_fractions():
    results = [
        make_result("fast", 10, 0.5),
        make_result("slow", 10, 1.0),
        make_result("fast", 20, 0.8),
        make_result("slow", 20, 1.5),
    ]
    rows = compute_win_rates(results)
    assert len(rows) == 1
    row = rows[0]
    assert row.win_rate_a == pytest.approx(1.0)
    assert row.win_rate_b == pytest.approx(0.0)


def test_render_winrate_table_empty():
    output = render_winrate_table([])
    assert "No win-rate" in output


def test_render_winrate_table_contains_commands():
    rows = [
        WinRateRow("cmd_a", "cmd_b", 3, 1, 0, 4, 0.75, 0.25)
    ]
    output = render_winrate_table(rows)
    assert "cmd_a" in output
    assert "cmd_b" in output
    assert "75.0%" in output
