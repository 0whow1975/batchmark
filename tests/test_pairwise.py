"""Tests for batchmark.pairwise."""
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.pairwise import compare_pair, render_pairwise_table, PairwiseRow


def make_result(command, size, times, error=None):
    return BenchmarkResult(
        command=command,
        size=size,
        times=times,
        returncode=0 if error is None else 1,
        error=error,
    )


def test_compare_pair_basic():
    results = [
        make_result("cmd_a", 100, [1.0, 1.0, 1.0]),
        make_result("cmd_b", 100, [2.0, 2.0, 2.0]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    assert len(rows) == 1
    row = rows[0]
    assert row.size == 100
    assert row.mean_a == pytest.approx(1.0)
    assert row.mean_b == pytest.approx(2.0)
    assert row.delta == pytest.approx(1.0)
    assert row.ratio == pytest.approx(2.0)
    assert row.winner == "a"


def test_compare_pair_b_wins():
    results = [
        make_result("cmd_a", 50, [3.0, 3.0]),
        make_result("cmd_b", 50, [1.0, 1.0]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    assert rows[0].winner == "b"


def test_compare_pair_tie():
    results = [
        make_result("cmd_a", 200, [1.0, 1.0]),
        make_result("cmd_b", 200, [1.01, 1.01]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b", tie_threshold=0.02)
    assert rows[0].winner == "tie"


def test_compare_pair_skips_failures():
    results = [
        make_result("cmd_a", 100, [], error="timeout"),
        make_result("cmd_b", 100, [1.0]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    assert rows == []


def test_compare_pair_no_shared_sizes():
    results = [
        make_result("cmd_a", 100, [1.0]),
        make_result("cmd_b", 200, [1.0]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    assert rows == []


def test_compare_pair_multiple_sizes():
    results = [
        make_result("cmd_a", 100, [1.0]),
        make_result("cmd_a", 200, [2.0]),
        make_result("cmd_b", 100, [1.5]),
        make_result("cmd_b", 200, [1.8]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    assert len(rows) == 2
    assert rows[0].size == 100
    assert rows[1].size == 200
    assert rows[0].winner == "a"   # b is slower at 100
    assert rows[1].winner == "b"   # b is faster at 200


def test_render_pairwise_table_empty():
    assert render_pairwise_table([]) == "No pairwise data available."


def test_render_pairwise_table_contains_summary():
    results = [
        make_result("cmd_a", 100, [1.0]),
        make_result("cmd_b", 100, [2.0]),
    ]
    rows = compare_pair(results, "cmd_a", "cmd_b")
    table = render_pairwise_table(rows)
    assert "Summary" in table
    assert "cmd_a" in table
    assert "cmd_b" in table
    assert "100" in table
