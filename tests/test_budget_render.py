"""Additional rendering and edge-case tests for batchmark.budget."""

import pytest
from batchmark.budget import check_budget, render_budget_table
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


def test_render_table_contains_command():
    results = [make_result(command="sort", mean=0.8)]
    brs = check_budget(results, budget=1.0)
    table = render_budget_table(brs)
    assert "sort" in table


def test_render_table_contains_size():
    results = [make_result(size=512, mean=0.8)]
    brs = check_budget(results, budget=1.0)
    table = render_budget_table(brs)
    assert "512" in table


def test_render_table_delta_sign_positive():
    results = [make_result(mean=2.5)]
    brs = check_budget(results, budget=1.0)
    table = render_budget_table(brs)
    assert "+" in table  # positive delta shown with sign


def test_budget_exact_equals_not_exceeded():
    results = [make_result(mean=1.0)]
    brs = check_budget(results, budget=1.0)
    assert not brs[0].exceeded
    assert pytest.approx(brs[0].delta, abs=1e-9) == 0.0


def test_budget_multiple_commands_no_filter():
    results = [
        make_result(command="grep", mean=0.5),
        make_result(command="awk", mean=1.5),
        make_result(command="sed", mean=0.9),
    ]
    brs = check_budget(results, budget=1.0)
    assert len(brs) == 3
    exceeded = [br for br in brs if br.exceeded]
    assert len(exceeded) == 1
    assert exceeded[0].result.command == "awk"


def test_render_summary_line_format():
    results = [
        make_result(mean=0.5),
        make_result(size=200, mean=1.5),
        make_result(size=300, mean=2.0),
    ]
    brs = check_budget(results, budget=1.0)
    table = render_budget_table(brs)
    assert "2/3 results exceeded" in table
