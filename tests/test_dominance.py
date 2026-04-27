"""Tests for batchmark.dominance."""

import pytest
from batchmark.runner import BenchmarkResult
from batchmark.dominance import compute_dominance, render_dominance_table, DominanceRow


def make_result(cmd, size, mean_time, success=True):
    return BenchmarkResult(
        command=cmd,
        input_size=size,
        times=[mean_time],
        mean_time=mean_time,
        median_time=mean_time,
        stdev_time=0.0,
        min_time=mean_time,
        max_time=mean_time,
        success=success,
        exit_code=0 if success else 1,
        timed_out=False,
    )


def test_compute_dominance_basic():
    results = [
        make_result("fast", 100, 1.0),
        make_result("fast", 200, 2.0),
        make_result("slow", 100, 3.0),
        make_result("slow", 200, 6.0),
    ]
    rows = compute_dominance(results)
    assert len(rows) == 1
    assert rows[0].winner == "fast"
    assert rows[0].loser == "slow"
    assert rows[0].sizes_compared == 2
    assert rows[0].strict is True


def test_compute_dominance_no_dominance():
    # cmd_a wins at size 100, cmd_b wins at size 200 — no dominance
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 5.0),
        make_result("cmd_b", 100, 3.0),
        make_result("cmd_b", 200, 2.0),
    ]
    rows = compute_dominance(results)
    assert rows == []


def test_compute_dominance_skips_failures():
    results = [
        make_result("fast", 100, 1.0),
        make_result("fast", 200, 2.0),
        make_result("slow", 100, 3.0, success=False),
        make_result("slow", 200, 6.0),
    ]
    # Only one shared size (200) — fast still dominates with one point
    rows = compute_dominance(results)
    assert len(rows) == 1
    assert rows[0].sizes_compared == 1


def test_compute_dominance_command_filter():
    results = [
        make_result("fast", 100, 1.0),
        make_result("slow", 100, 3.0),
        make_result("medium", 100, 2.0),
    ]
    rows = compute_dominance(results, command_filter=["fast", "slow"])
    assert all(r.winner in ("fast", "slow") and r.loser in ("fast", "slow") for r in rows)
    cmds_seen = {r.winner for r in rows} | {r.loser for r in rows}
    assert "medium" not in cmds_seen


def test_compute_dominance_non_strict():
    # cmd_a ties at one size, wins at another — non-strict dominance
    results = [
        make_result("cmd_a", 100, 2.0),
        make_result("cmd_a", 200, 2.0),
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_b", 200, 4.0),
    ]
    rows = compute_dominance(results)
    assert len(rows) == 1
    assert rows[0].winner == "cmd_a"
    assert rows[0].strict is False


def test_render_dominance_table_empty():
    output = render_dominance_table([])
    assert "No dominance" in output


def test_render_dominance_table_contains_winner():
    rows = [
        DominanceRow(
            winner="fast",
            loser="slow",
            sizes_compared=3,
            max_speedup=4.0,
            min_speedup=2.0,
            avg_speedup=3.0,
            strict=True,
        )
    ]
    output = render_dominance_table(rows)
    assert "fast" in output
    assert "slow" in output
    assert "yes" in output
