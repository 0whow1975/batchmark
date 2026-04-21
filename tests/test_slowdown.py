"""Tests for batchmark.slowdown and batchmark.cli_slowdown."""

from __future__ import annotations

import argparse
import io
import json
from unittest.mock import patch

from batchmark.runner import BenchmarkResult
from batchmark.slowdown import detect_slowdowns, render_slowdown_table
from batchmark.cli_slowdown import build_slowdown_parser, run_slowdown


def make_result(command="cmd", size=1, elapsed=1.0, success=True, runs=3):
    return BenchmarkResult(
        command=command,
        size=size,
        times=[elapsed] * runs,
        success=success,
        exit_code=0 if success else 1,
    )


# ---------------------------------------------------------------------------
# detect_slowdowns
# ---------------------------------------------------------------------------

def test_detect_slowdowns_basic():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=3.0),
        make_result(size=1000, elapsed=10.0),
    ]
    rows = detect_slowdowns(results, threshold=2.0)
    assert len(rows) == 3
    # baseline row (size=10) ratio == 1.0
    baseline_row = next(r for r in rows if r.size == 10)
    assert baseline_row.ratio == 1.0
    assert not baseline_row.flagged
    # size=1000 should be flagged (ratio=10)
    big_row = next(r for r in rows if r.size == 1000)
    assert big_row.flagged
    assert abs(big_row.ratio - 10.0) < 1e-9


def test_detect_slowdowns_no_regression():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=1.5),
    ]
    rows = detect_slowdowns(results, threshold=3.0)
    assert all(not r.flagged for r in rows)


def test_detect_slowdowns_skips_failures():
    results = [
        make_result(size=10, elapsed=1.0, success=False),
        make_result(size=100, elapsed=5.0, success=False),
    ]
    rows = detect_slowdowns(results)
    assert rows == []


def test_detect_slowdowns_too_few_sizes():
    # Only one distinct size — nothing to compare against.
    results = [make_result(size=10, elapsed=1.0)] * 3
    rows = detect_slowdowns(results)
    assert rows == []


def test_detect_slowdowns_multiple_commands():
    results = [
        make_result(command="fast", size=10, elapsed=1.0),
        make_result(command="fast", size=100, elapsed=1.2),
        make_result(command="slow", size=10, elapsed=1.0),
        make_result(command="slow", size=100, elapsed=5.0),
    ]
    rows = detect_slowdowns(results, threshold=2.0)
    slow_rows = [r for r in rows if r.command == "slow" and r.flagged]
    fast_rows = [r for r in rows if r.command == "fast" and r.flagged]
    assert len(slow_rows) == 1
    assert len(fast_rows) == 0


# ---------------------------------------------------------------------------
# render_slowdown_table
# ---------------------------------------------------------------------------

def test_render_slowdown_table_empty():
    assert render_slowdown_table([]) == "No slowdown data."


def test_render_slowdown_table_contains_flag():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=5.0),
    ]
    rows = detect_slowdowns(results, threshold=2.0)
    table = render_slowdown_table(rows)
    assert "YES" in table
    assert "cmd" in table


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_slowdown_parser_defaults():
    p = build_slowdown_parser()
    args = p.parse_args(["history.json"])
    assert args.threshold == 2.0
    assert args.format == "table"
    assert not args.flagged_only
    assert args.tag is None


def test_run_slowdown_table_output():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=4.0),
    ]
    args = argparse.Namespace(
        history_file="dummy.json",
        threshold=2.0,
        tag=None,
        flagged_only=False,
        format="table",
    )
    out = io.StringIO()
    with patch("batchmark.cli_slowdown.load_results", return_value=results):
        run_slowdown(args, out=out)
    assert "cmd" in out.getvalue()


def test_run_slowdown_json_output():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=6.0),
    ]
    args = argparse.Namespace(
        history_file="dummy.json",
        threshold=2.0,
        tag=None,
        flagged_only=False,
        format="json",
    )
    out = io.StringIO()
    with patch("batchmark.cli_slowdown.load_results", return_value=results):
        run_slowdown(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"


def test_run_slowdown_flagged_only():
    results = [
        make_result(size=10, elapsed=1.0),
        make_result(size=100, elapsed=1.1),   # ratio < 2 → not flagged
        make_result(size=1000, elapsed=10.0),  # ratio = 10 → flagged
    ]
    args = argparse.Namespace(
        history_file="dummy.json",
        threshold=2.0,
        tag=None,
        flagged_only=True,
        format="json",
    )
    out = io.StringIO()
    with patch("batchmark.cli_slowdown.load_results", return_value=results):
        run_slowdown(args, out=out)
    data = json.loads(out.getvalue())
    assert all(d["flagged"] for d in data)
