"""Tests for batchmark.speedup and batchmark.cli_speedup."""

import io
import json
from unittest.mock import patch

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.speedup import SpeedupRow, compute_speedup, render_speedup_table
from batchmark.cli_speedup import build_speedup_parser, run_speedup


def make_result(cmd, size, times, success=True):
    r = BenchmarkResult(command=cmd, size=size, times=times, success=success)
    return r


# ---------------------------------------------------------------------------
# compute_speedup
# ---------------------------------------------------------------------------

def test_compute_speedup_basic():
    results = [
        make_result("fast_cmd", 100, [1.0, 1.0]),
        make_result("slow_cmd", 100, [2.0, 2.0]),
    ]
    rows = compute_speedup(results, baseline_command="slow_cmd")
    assert len(rows) == 1
    row = rows[0]
    assert row.command == "fast_cmd"
    assert row.size == 100
    assert row.speedup == pytest.approx(2.0)
    assert row.faster is True


def test_compute_speedup_slower_target():
    results = [
        make_result("base", 50, [1.0]),
        make_result("worse", 50, [3.0]),
    ]
    rows = compute_speedup(results, baseline_command="base")
    assert rows[0].speedup == pytest.approx(1.0 / 3.0)
    assert rows[0].faster is False


def test_compute_speedup_skips_failures():
    results = [
        make_result("base", 10, [1.0]),
        make_result("other", 10, [], success=False),
    ]
    rows = compute_speedup(results, baseline_command="base")
    assert rows == []


def test_compute_speedup_missing_size():
    """Target has a size the baseline doesn't — should be skipped."""
    results = [
        make_result("base", 10, [1.0]),
        make_result("other", 20, [0.5]),  # size 20 not in baseline
    ]
    rows = compute_speedup(results, baseline_command="base")
    assert rows == []


def test_compute_speedup_multiple_sizes():
    results = [
        make_result("base", 10, [2.0]),
        make_result("base", 20, [4.0]),
        make_result("other", 10, [1.0]),
        make_result("other", 20, [2.0]),
    ]
    rows = compute_speedup(results, baseline_command="base")
    assert len(rows) == 2
    assert all(r.speedup == pytest.approx(2.0) for r in rows)


# ---------------------------------------------------------------------------
# render_speedup_table
# ---------------------------------------------------------------------------

def test_render_speedup_table_empty():
    out = render_speedup_table([], baseline_command="base")
    assert "No speedup" in out


def test_render_speedup_table_contains_command():
    rows = [SpeedupRow(command="fast", size=100, baseline_mean=2.0, target_mean=1.0, speedup=2.0, faster=True)]
    out = render_speedup_table(rows, baseline_command="slow")
    assert "fast" in out
    assert "2.000x" in out
    assert "yes" in out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_speedup_parser_defaults():
    p = build_speedup_parser()
    args = p.parse_args(["history.json", "base_cmd"])
    assert args.history_file == "history.json"
    assert args.baseline == "base_cmd"
    assert args.format == "table"
    assert args.tag is None


def test_run_speedup_table_output():
    results = [
        make_result("base", 10, [2.0]),
        make_result("fast", 10, [1.0]),
    ]
    p = build_speedup_parser()
    args = p.parse_args(["dummy.json", "base"])
    buf = io.StringIO()
    with patch("batchmark.cli_speedup.load_results", return_value=results):
        rc = run_speedup(args, out=buf)
    assert rc == 0
    assert "fast" in buf.getvalue()


def test_run_speedup_json_output():
    results = [
        make_result("base", 10, [2.0]),
        make_result("fast", 10, [1.0]),
    ]
    p = build_speedup_parser()
    args = p.parse_args(["dummy.json", "base", "--format", "json"])
    buf = io.StringIO()
    with patch("batchmark.cli_speedup.load_results", return_value=results):
        run_speedup(args, out=buf)
    data = json.loads(buf.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "fast"
    assert data[0]["speedup"] == pytest.approx(2.0)
