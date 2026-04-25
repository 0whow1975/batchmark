"""Tests for batchmark.breakeven."""
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.breakeven import find_breakeven, render_breakeven_table


def make_result(cmd, size, mean, success=True):
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


def test_find_breakeven_crossover():
    # cmd_a starts fast, cmd_b overtakes at size 200
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 2.0),
        make_result("cmd_a", 300, 3.0),
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_b", 200, 2.0),
        make_result("cmd_b", 300, 1.5),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    assert r.command_a == "cmd_a"
    assert r.command_b == "cmd_b"
    assert r.breakeven_size is not None
    assert 200.0 <= r.breakeven_size <= 300.0
    assert r.a_wins_below is True  # cmd_a faster at size 100


def test_find_breakeven_no_crossover_a_always_faster():
    results = [
        make_result("cmd_a", 100, 0.5),
        make_result("cmd_a", 200, 1.0),
        make_result("cmd_b", 100, 1.0),
        make_result("cmd_b", 200, 2.0),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    assert r.breakeven_size is None
    assert r.a_wins_below is True


def test_find_breakeven_no_crossover_b_always_faster():
    results = [
        make_result("cmd_a", 100, 2.0),
        make_result("cmd_a", 200, 4.0),
        make_result("cmd_b", 100, 1.0),
        make_result("cmd_b", 200, 2.0),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    assert r.breakeven_size is None
    assert r.a_wins_below is False


def test_find_breakeven_skips_failures():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 2.0, success=False),  # skipped
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_b", 200, 1.0),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    # only size 100 is common; no crossover possible
    assert r.breakeven_size is None
    assert r.sizes_a == [100]
    assert r.sizes_b == [100, 200]


def test_find_breakeven_exact_crossover_at_boundary():
    # Equal at size 200 exactly
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 2.0),
        make_result("cmd_a", 300, 3.0),
        make_result("cmd_b", 100, 3.0),
        make_result("cmd_b", 200, 2.0),
        make_result("cmd_b", 300, 1.0),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    assert r.breakeven_size == pytest.approx(200.0)


def test_render_breakeven_table_with_crossover():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 300, 3.0),
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_b", 300, 1.0),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    table = render_breakeven_table(r)
    assert "cmd_a" in table
    assert "cmd_b" in table
    assert "Crossover" in table


def test_render_breakeven_table_no_crossover():
    results = [
        make_result("cmd_a", 100, 0.5),
        make_result("cmd_b", 100, 1.5),
    ]
    r = find_breakeven(results, "cmd_a", "cmd_b")
    table = render_breakeven_table(r)
    assert "No crossover" in table
    assert "cmd_a" in table
