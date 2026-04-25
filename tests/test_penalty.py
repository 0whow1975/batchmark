"""Tests for batchmark.penalty."""
from __future__ import annotations

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.penalty import PenaltyRow, compute_penalty, render_penalty_table


def make_result(command: str, size: int, mean: float, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=command,
        size=size,
        times=[mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        success=success,
    )


def test_compute_penalty_basic():
    results = [
        make_result("fast", 100, 0.5),
        make_result("slow", 100, 2.0),
    ]
    rows = compute_penalty(results)
    assert len(rows) == 2
    assert rows[0].command == "fast"
    assert rows[0].rank == 1
    assert rows[1].command == "slow"
    assert rows[1].rank == 2


def test_compute_penalty_rank_order():
    results = [
        make_result("b", 100, 3.0),
        make_result("a", 100, 1.0),
        make_result("c", 100, 2.0),
    ]
    rows = compute_penalty(results)
    assert [r.command for r in rows] == ["a", "c", "b"]
    assert [r.rank for r in rows] == [1, 2, 3]


def test_compute_penalty_skips_failures_in_mean():
    results = [
        make_result("cmd", 100, 1.0, success=True),
        make_result("cmd", 200, 0.0, success=False),
    ]
    rows = compute_penalty(results)
    assert len(rows) == 1
    row = rows[0]
    assert row.failure_rate == pytest.approx(0.5)
    assert row.mean == pytest.approx(1.0)


def test_compute_penalty_all_failures():
    results = [
        make_result("bad", 100, 0.0, success=False),
    ]
    rows = compute_penalty(results)
    assert rows[0].mean == pytest.approx(0.0)
    assert rows[0].failure_rate == pytest.approx(1.0)
    assert rows[0].score == pytest.approx(2.0)  # w_failure=2.0 * 1.0


def test_compute_penalty_custom_weights():
    results = [
        make_result("a", 100, 1.0),
        make_result("b", 100, 2.0),
    ]
    rows = compute_penalty(results, w_mean=10.0, w_stdev=0.0, w_failure=0.0)
    assert rows[0].command == "a"
    assert rows[0].score == pytest.approx(10.0)
    assert rows[1].score == pytest.approx(20.0)


def test_compute_penalty_empty():
    rows = compute_penalty([])
    assert rows == []


def test_render_penalty_table_basic():
    results = [make_result("mycmd", 100, 1.23)]
    rows = compute_penalty(results)
    table = render_penalty_table(rows)
    assert "mycmd" in table
    assert "Rank" in table
    assert "Score" in table


def test_render_penalty_table_empty():
    assert render_penalty_table([]) == "No penalty data."
