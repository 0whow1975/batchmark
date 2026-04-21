"""Tests for batchmark.variance and batchmark.cli_variance."""

import json
from io import StringIO
from unittest.mock import patch
import pytest

from batchmark.runner import BenchmarkResult
from batchmark.variance import analyze_variance, render_variance_table, _stability_label
from batchmark.cli_variance import build_variance_parser, run_variance


def make_result(cmd="sort", size=100, elapsed=1.0, exit_code=0):
    return BenchmarkResult(
        command=cmd,
        size=size,
        elapsed=elapsed,
        exit_code=exit_code,
        runs=[elapsed],
        stdout="",
        stderr="",
    )


def test_stability_label_stable():
    assert _stability_label(2.0) == "stable"


def test_stability_label_moderate():
    assert _stability_label(10.0) == "moderate"


def test_stability_label_unstable():
    assert _stability_label(25.0) == "unstable"


def test_analyze_variance_basic():
    results = [
        make_result(cmd="sort", size=100, elapsed=1.0),
        make_result(cmd="sort", size=200, elapsed=1.1),
        make_result(cmd="sort", size=300, elapsed=1.05),
    ]
    rows = analyze_variance(results)
    assert len(rows) == 1
    row = rows[0]
    assert row.command == "sort"
    assert row.sample_count == 3
    assert row.mean_time == pytest.approx(1.05, rel=1e-2)
    assert row.stability in ("stable", "moderate")


def test_analyze_variance_skips_failures():
    results = [
        make_result(cmd="grep", elapsed=2.0, exit_code=1),
        make_result(cmd="grep", elapsed=2.1, exit_code=0),
        make_result(cmd="grep", elapsed=2.2, exit_code=0),
    ]
    rows = analyze_variance(results)
    assert rows[0].sample_count == 2


def test_analyze_variance_command_filter():
    results = [
        make_result(cmd="sort", elapsed=1.0),
        make_result(cmd="sort", elapsed=1.1),
        make_result(cmd="grep", elapsed=2.0),
        make_result(cmd="grep", elapsed=2.1),
    ]
    rows = analyze_variance(results, command_filter="grep")
    assert all(r.command == "grep" for r in rows)
    assert len(rows) == 1


def test_analyze_variance_too_few_points():
    results = [make_result(cmd="solo", elapsed=1.0)]
    rows = analyze_variance(results)
    assert rows == []


def test_render_variance_table_empty():
    assert "No variance" in render_variance_table([])


def test_render_variance_table_contains_command():
    results = [
        make_result(cmd="myapp", elapsed=0.5),
        make_result(cmd="myapp", elapsed=0.6),
    ]
    rows = analyze_variance(results)
    table = render_variance_table(rows)
    assert "myapp" in table
    assert "CV%" in table


def test_run_variance_table_output():
    results = [
        make_result(cmd="cmd", elapsed=1.0),
        make_result(cmd="cmd", elapsed=1.2),
    ]
    args = build_variance_parser().parse_args(["history.json", "--format", "table"])
    out = StringIO()
    with patch("batchmark.cli_variance.load_results", return_value=results):
        code = run_variance(args, out=out)
    assert "cmd" in out.getvalue()
    assert isinstance(code, int)


def test_run_variance_json_output():
    results = [
        make_result(cmd="cmd", elapsed=1.0),
        make_result(cmd="cmd", elapsed=3.0),
    ]
    args = build_variance_parser().parse_args(["history.json", "--format", "json"])
    out = StringIO()
    with patch("batchmark.cli_variance.load_results", return_value=results):
        run_variance(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"
    assert "cv_percent" in data[0]
