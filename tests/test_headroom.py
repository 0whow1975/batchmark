"""Tests for batchmark.headroom and batchmark.cli_headroom."""
from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from batchmark.headroom import (
    HeadroomResult,
    compute_headroom,
    render_headroom_table,
)
from batchmark.runner import BenchmarkResult


def make_result(cmd: str, size: int, times, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(command=cmd, size=size, times=list(times), success=success, error=None)


# ---------------------------------------------------------------------------
# compute_headroom
# ---------------------------------------------------------------------------

def test_compute_headroom_within_budget():
    results = [make_result("cmd_a", 100, [0.1, 0.2, 0.1])]
    rows = compute_headroom(results, budget=0.5)
    assert len(rows) == 1
    r = rows[0]
    assert r.within_budget is True
    assert pytest.approx(r.mean_time, abs=1e-6) == pytest.approx((0.1 + 0.2 + 0.1) / 3)
    assert pytest.approx(r.headroom, abs=1e-6) == 0.5 - r.mean_time


def test_compute_headroom_over_budget():
    results = [make_result("cmd_a", 100, [1.0, 1.2, 1.1])]
    rows = compute_headroom(results, budget=0.5)
    assert len(rows) == 1
    assert rows[0].within_budget is False
    assert rows[0].headroom < 0


def test_compute_headroom_skips_failures():
    results = [
        make_result("cmd_a", 100, [0.1], success=False),
        make_result("cmd_b", 200, [0.2], success=True),
    ]
    rows = compute_headroom(results, budget=1.0)
    assert len(rows) == 1
    assert rows[0].command == "cmd_b"


def test_compute_headroom_command_filter():
    results = [
        make_result("cmd_a", 100, [0.1]),
        make_result("cmd_b", 100, [0.2]),
    ]
    rows = compute_headroom(results, budget=1.0, command="cmd_a")
    assert all(r.command == "cmd_a" for r in rows)


def test_compute_headroom_sorted():
    results = [
        make_result("cmd_b", 200, [0.2]),
        make_result("cmd_a", 100, [0.1]),
        make_result("cmd_a", 50, [0.05]),
    ]
    rows = compute_headroom(results, budget=1.0)
    keys = [(r.command, r.size) for r in rows]
    assert keys == sorted(keys)


def test_compute_headroom_pct():
    results = [make_result("cmd", 1, [0.25])]
    rows = compute_headroom(results, budget=1.0)
    assert pytest.approx(rows[0].headroom_pct) == 75.0


# ---------------------------------------------------------------------------
# render_headroom_table
# ---------------------------------------------------------------------------

def test_render_headroom_table_empty():
    assert render_headroom_table([]) == "No headroom data."


def test_render_headroom_table_contains_command():
    results = [make_result("my_cmd", 512, [0.3])]
    rows = compute_headroom(results, budget=1.0)
    table = render_headroom_table(rows)
    assert "my_cmd" in table
    assert "512" in table


def test_render_headroom_table_flags_over_budget():
    results = [make_result("slow", 100, [2.0])]
    rows = compute_headroom(results, budget=1.0)
    table = render_headroom_table(rows)
    assert "NO" in table


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_run_headroom_table_output():
    from batchmark.cli_headroom import build_headroom_parser, run_headroom

    results = [make_result("cmd", 100, [0.1, 0.2])]
    args = build_headroom_parser().parse_args(["dummy.json", "--budget", "1.0"])
    out = StringIO()
    with patch("batchmark.cli_headroom.load_results", return_value=results):
        rc = run_headroom(args, out=out)
    assert rc == 0
    assert "cmd" in out.getvalue()


def test_run_headroom_json_output():
    from batchmark.cli_headroom import build_headroom_parser, run_headroom

    results = [make_result("cmd", 100, [0.5])]
    args = build_headroom_parser().parse_args(["dummy.json", "--budget", "1.0", "--format", "json"])
    out = StringIO()
    with patch("batchmark.cli_headroom.load_results", return_value=results):
        run_headroom(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"


def test_run_headroom_fail_on_over():
    from batchmark.cli_headroom import build_headroom_parser, run_headroom

    results = [make_result("slow", 100, [2.0])]
    args = build_headroom_parser().parse_args(["dummy.json", "--budget", "1.0", "--fail-on-over"])
    out = StringIO()
    with patch("batchmark.cli_headroom.load_results", return_value=results):
        rc = run_headroom(args, out=out)
    assert rc == 1
