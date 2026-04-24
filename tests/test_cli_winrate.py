"""Tests for batchmark.cli_winrate."""
import io
import json
import pytest
from unittest.mock import patch
from batchmark.runner import BenchmarkResult
from batchmark.cli_winrate import build_winrate_parser, run_winrate


def make_result(command, size, mean_time, success=True):
    return BenchmarkResult(
        command=command,
        size=size,
        times=[mean_time],
        mean_time=mean_time,
        median_time=mean_time,
        stdev_time=0.0,
        min_time=mean_time,
        max_time=mean_time,
        success=success,
        error=None,
    )


def test_build_winrate_parser_defaults():
    parser = build_winrate_parser()
    args = parser.parse_args(["results.json"])
    assert args.history_file == "results.json"
    assert args.tag is None
    assert args.format == "table"


def test_build_winrate_parser_all_flags():
    parser = build_winrate_parser()
    args = parser.parse_args(["results.json", "--tag", "v1", "--format", "json"])
    assert args.tag == "v1"
    assert args.format == "json"


def test_run_winrate_table_output():
    results = [
        make_result("alpha", 100, 1.0),
        make_result("beta", 100, 2.0),
    ]
    parser = build_winrate_parser()
    args = parser.parse_args(["dummy.json"])
    out = io.StringIO()
    with patch("batchmark.cli_winrate.load_results", return_value=results):
        run_winrate(args, out=out)
    output = out.getvalue()
    assert "alpha" in output
    assert "beta" in output


def test_run_winrate_json_output():
    results = [
        make_result("alpha", 100, 1.0),
        make_result("beta", 100, 2.0),
    ]
    parser = build_winrate_parser()
    args = parser.parse_args(["dummy.json", "--format", "json"])
    out = io.StringIO()
    with patch("batchmark.cli_winrate.load_results", return_value=results):
        run_winrate(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["command_a"] == "alpha"
    assert data[0]["wins_a"] == 1


def test_run_winrate_empty():
    parser = build_winrate_parser()
    args = parser.parse_args(["dummy.json"])
    out = io.StringIO()
    with patch("batchmark.cli_winrate.load_results", return_value=[]):
        run_winrate(args, out=out)
    assert "No win-rate" in out.getvalue()
