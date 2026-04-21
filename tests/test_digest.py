"""Tests for batchmark.digest and batchmark.cli_digest."""

import json
import io
import pytest
from unittest.mock import patch

from batchmark.runner import BenchmarkResult
from batchmark.digest import build_digest, render_digest_table
from batchmark.cli_digest import build_digest_parser, run_digest


def make_result(cmd="cmd", size=1, elapsed=1.0, exit_code=0):
    return BenchmarkResult(
        command=cmd,
        size=size,
        elapsed=elapsed,
        exit_code=exit_code,
        stdout="",
        stderr="",
        timed_out=False,
    )


def test_build_digest_basic():
    results = [
        make_result("cmd_a", elapsed=1.0),
        make_result("cmd_a", elapsed=3.0),
        make_result("cmd_b", elapsed=2.0),
    ]
    entries = build_digest(results)
    assert len(entries) == 2
    cmds = [e.command for e in entries]
    assert "cmd_a" in cmds and "cmd_b" in cmds


def test_build_digest_stats():
    results = [make_result("x", elapsed=t) for t in [1.0, 2.0, 3.0, 4.0]]
    entries = build_digest(results)
    assert len(entries) == 1
    e = entries[0]
    assert e.sample_count == 4
    assert e.mean_time == pytest.approx(2.5)
    assert e.min_time == pytest.approx(1.0)
    assert e.failure_count == 0
    assert e.success_rate == pytest.approx(1.0)


def test_build_digest_skips_failures():
    results = [
        make_result("cmd", elapsed=2.0, exit_code=0),
        make_result("cmd", elapsed=None, exit_code=1),
    ]
    entries = build_digest(results)
    assert len(entries) == 1
    e = entries[0]
    assert e.sample_count == 1
    assert e.failure_count == 1
    assert e.success_rate == pytest.approx(0.5)


def test_build_digest_empty():
    assert build_digest([]) == []


def test_render_digest_table_contains_command():
    results = [make_result("my_command", elapsed=1.5)]
    entries = build_digest(results)
    table = render_digest_table(entries)
    assert "my_command" in table
    assert "Mean" in table


def test_render_digest_table_empty():
    assert "No digest" in render_digest_table([])


def test_run_digest_table_output():
    results = [make_result("grep", elapsed=0.5), make_result("grep", elapsed=0.7)]
    parser = build_digest_parser()
    args = parser.parse_args(["history.json"])
    out = io.StringIO()
    with patch("batchmark.cli_digest.load_results", return_value=results):
        code = run_digest(args, out=out)
    assert code == 0
    assert "grep" in out.getvalue()


def test_run_digest_json_output():
    results = [make_result("sort", elapsed=1.2)]
    parser = build_digest_parser()
    args = parser.parse_args(["history.json", "--format", "json"])
    out = io.StringIO()
    with patch("batchmark.cli_digest.load_results", return_value=results):
        run_digest(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "sort"
    assert "mean_time" in data[0]


def test_run_digest_no_results():
    parser = build_digest_parser()
    args = parser.parse_args(["history.json"])
    out = io.StringIO()
    with patch("batchmark.cli_digest.load_results", return_value=[]):
        code = run_digest(args, out=out)
    assert code == 0
    assert "No results" in out.getvalue()
