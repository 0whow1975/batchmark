"""Tests for batchmark.budget."""

import pytest
from batchmark.budget import check_budget, render_budget_table, BudgetResult
from batchmark.runner import BenchmarkResult


def make_result(command="cmd", size=100, mean=1.0, failed=False):
    return BenchmarkResult(
        command=command,
        size=size,
        times=[] if failed else [mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        failed=failed,
    )


def test_check_budget_under():
    results = [make_result(mean=0.5)]
    out = check_budget(results, budget=1.0)
    assert len(out) == 1
    assert not out[0].exceeded
    assert pytest.approx(out[0].delta, abs=1e-9) == -0.5


def test_check_budget_over():
    results = [make_result(mean=2.0)]
    out = check_budget(results, budget=1.0)
    assert len(out) == 1
    assert out[0].exceeded
    assert pytest.approx(out[0].delta, abs=1e-9) == 1.0


def test_check_budget_skips_failures():
    results = [make_result(failed=True), make_result(mean=0.5)]
    out = check_budget(results, budget=1.0)
    assert len(out) == 1
    assert not out[0].result.failed


def test_check_budget_command_filter():
    results = [
        make_result(command="grep", mean=0.5),
        make_result(command="awk", mean=2.0),
    ]
    out = check_budget(results, budget=1.0, command="grep")
    assert len(out) == 1
    assert out[0].result.command == "grep"


def test_check_budget_empty():
    assert check_budget([], budget=1.0) == []


def test_render_budget_table_basic():
    results = [
        make_result(command="grep", size=100, mean=0.5),
        make_result(command="grep", size=200, mean=1.5),
    ]
    budget_results = check_budget(results, budget=1.0)
    table = render_budget_table(budget_results)
    assert "OK" in table
    assert "OVER" in table
    assert "1/2 results exceeded" in table


def test_render_budget_table_empty():
    assert render_budget_table([]) == "No results to display."


def test_render_budget_table_all_ok():
    results = [make_result(mean=0.1), make_result(size=200, mean=0.2)]
    budget_results = check_budget(results, budget=1.0)
    table = render_budget_table(budget_results)
    assert "0/2 results exceeded" in table
