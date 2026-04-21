"""Tests for batchmark.bottleneck."""
from __future__ import annotations

import json
import io
from unittest.mock import patch

import pytest

from batchmark.bottleneck import (
    BottleneckEntry,
    find_bottlenecks,
    render_bottleneck_table,
)
from batchmark.cli_bottleneck import build_bottleneck_parser, run_bottleneck
from batchmark.runner import BenchmarkResult


def make_result(command="cmd", size=100, times=None, success=True):
    return BenchmarkResult(
        command=command,
        size=size,
        times=times if times is not None else [1.0],
        success=success,
        exit_code=0 if success else 1,
        error=None,
    )


def test_find_bottlenecks_basic():
    results = [
        make_result("fast", 100, [0.1, 0.1]),
        make_result("slow", 100, [0.9, 0.9]),
    ]
    entries = find_bottlenecks(results, threshold=0.5)
    assert entries[0].command == "slow"
    assert entries[0].is_bottleneck is True
    assert entries[1].command == "fast"
    assert entries[1].is_bottleneck is False


def test_find_bottlenecks_share_sums_to_one():
    results = [
        make_result("a", 10, [1.0]),
        make_result("b", 10, [3.0]),
    ]
    entries = find_bottlenecks(results, threshold=0.0)
    total = sum(e.total_share for e in entries)
    assert abs(total - 1.0) < 1e-9


def test_find_bottlenecks_skips_failures():
    results = [
        make_result("ok", 50, [2.0]),
        make_result("bad", 50, [999.0], success=False),
    ]
    entries = find_bottlenecks(results)
    assert all(e.command == "ok" for e in entries)


def test_find_bottlenecks_empty():
    assert find_bottlenecks([]) == []


def test_find_bottlenecks_all_failures():
    results = [make_result("x", 1, [1.0], success=False)]
    assert find_bottlenecks(results) == []


def test_render_bottleneck_table_no_data():
    assert render_bottleneck_table([]) == "No data."


def test_render_bottleneck_table_contains_command():
    entries = [
        BottleneckEntry(command="mycmd", size=200, mean_time=1.5, total_share=0.75, is_bottleneck=True)
    ]
    out = render_bottleneck_table(entries)
    assert "mycmd" in out
    assert "BOTTLENECK" in out
    assert "75.0%" in out


def test_run_bottleneck_table(tmp_path):
    import json as _json
    from batchmark.history import save_results

    results = [
        make_result("alpha", 100, [0.5]),
        make_result("beta", 100, [1.5]),
    ]
    hist = tmp_path / "h.json"
    save_results(str(hist), results)

    parser = build_bottleneck_parser()
    args = parser.parse_args([str(hist), "--threshold", "0.6"])
    buf = io.StringIO()
    run_bottleneck(args, out=buf)
    output = buf.getvalue()
    assert "beta" in output
    assert "BOTTLENECK" in output


def test_run_bottleneck_json(tmp_path):
    from batchmark.history import save_results

    results = [make_result("cmd", 50, [2.0])]
    hist = tmp_path / "h.json"
    save_results(str(hist), results)

    parser = build_bottleneck_parser()
    args = parser.parse_args([str(hist), "--format", "json"])
    buf = io.StringIO()
    run_bottleneck(args, out=buf)
    data = json.loads(buf.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"
    assert "total_share" in data[0]
