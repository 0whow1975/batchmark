"""Tests for batchmark.fanout and batchmark.cli_fanout."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from batchmark.fanout import FanoutResult, compute_fanout, render_fanout_table
from batchmark.runner import BenchmarkResult


def make_result(command: str, size: int, mean_time: float, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=command,
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


def test_compute_fanout_basic():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 2.0),
        make_result("cmd_a", 400, 5.0),
    ]
    rows = compute_fanout(results, threshold=3.0)
    assert len(rows) == 1
    r = rows[0]
    assert r.command == "cmd_a"
    assert r.min_time == pytest.approx(1.0)
    assert r.max_time == pytest.approx(5.0)
    assert r.spread == pytest.approx(4.0)
    assert r.spread_ratio == pytest.approx(5.0)
    assert r.sizes_measured == 3
    assert r.flagged is True


def test_compute_fanout_no_flag_below_threshold():
    results = [
        make_result("cmd_b", 100, 2.0),
        make_result("cmd_b", 200, 3.0),
    ]
    rows = compute_fanout(results, threshold=5.0)
    assert len(rows) == 1
    assert rows[0].flagged is False


def test_compute_fanout_skips_failures():
    results = [
        make_result("cmd_c", 100, 1.0, success=False),
        make_result("cmd_c", 200, 3.0),
    ]
    # Only one successful result — not enough for fanout
    rows = compute_fanout(results)
    assert rows == []


def test_compute_fanout_command_filter():
    results = [
        make_result("cmd_a", 100, 1.0),
        make_result("cmd_a", 200, 5.0),
        make_result("cmd_b", 100, 1.0),
        make_result("cmd_b", 200, 2.0),
    ]
    rows = compute_fanout(results, command_filter="cmd_a")
    assert all(r.command == "cmd_a" for r in rows)
    assert len(rows) == 1


def test_compute_fanout_sorted_by_ratio_desc():
    results = [
        make_result("low", 100, 1.0),
        make_result("low", 200, 1.5),
        make_result("high", 100, 1.0),
        make_result("high", 200, 10.0),
    ]
    rows = compute_fanout(results)
    assert rows[0].command == "high"
    assert rows[1].command == "low"


def test_render_fanout_table_empty():
    assert render_fanout_table([]) == "No fanout data available."


def test_render_fanout_table_contains_command():
    rows = [
        FanoutResult(
            command="my_cmd", min_time=1.0, max_time=4.0,
            spread=3.0, spread_ratio=4.0, sizes_measured=3, flagged=True,
        )
    ]
    table = render_fanout_table(rows)
    assert "my_cmd" in table
    assert "YES" in table


def test_run_fanout_table_output():
    from batchmark.cli_fanout import build_fanout_parser, run_fanout

    results = [
        make_result("cmd_x", 100, 1.0),
        make_result("cmd_x", 500, 8.0),
    ]
    parser = build_fanout_parser()
    args = parser.parse_args(["dummy.json", "--threshold", "3.0"])
    out = StringIO()
    with patch("batchmark.cli_fanout.load_results", return_value=results):
        rc = run_fanout(args, out=out)
    assert rc == 0
    assert "cmd_x" in out.getvalue()


def test_run_fanout_json_output():
    from batchmark.cli_fanout import build_fanout_parser, run_fanout

    results = [
        make_result("cmd_y", 100, 1.0),
        make_result("cmd_y", 200, 4.0),
    ]
    parser = build_fanout_parser()
    args = parser.parse_args(["dummy.json", "--format", "json"])
    out = StringIO()
    with patch("batchmark.cli_fanout.load_results", return_value=results):
        run_fanout(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd_y"
    assert "spread_ratio" in data[0]
