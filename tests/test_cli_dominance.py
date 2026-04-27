"""Tests for batchmark.cli_dominance."""

import io
import json
import pytest
from unittest.mock import patch
from batchmark.runner import BenchmarkResult
from batchmark.cli_dominance import build_dominance_parser, run_dominance


def make_result(cmd, size, mean_time, success=True):
    return BenchmarkResult(
        command=cmd,
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


SAMPLE_RESULTS = [
    make_result("fast", 100, 1.0),
    make_result("fast", 200, 2.0),
    make_result("slow", 100, 3.0),
    make_result("slow", 200, 6.0),
]


def test_build_dominance_parser_defaults():
    p = build_dominance_parser()
    args = p.parse_args(["results.json"])
    assert args.history_file == "results.json"
    assert args.tag is None
    assert args.commands is None
    assert args.format == "table"
    assert args.strict_only is False


def test_build_dominance_parser_all_flags():
    p = build_dominance_parser()
    args = p.parse_args([
        "results.json",
        "--tag", "v1",
        "--command", "fast",
        "--command", "slow",
        "--format", "json",
        "--strict-only",
    ])
    assert args.tag == "v1"
    assert args.commands == ["fast", "slow"]
    assert args.format == "json"
    assert args.strict_only is True


def test_run_dominance_table_output():
    p = build_dominance_parser()
    args = p.parse_args(["results.json"])
    out = io.StringIO()
    with patch("batchmark.cli_dominance.load_results", return_value=SAMPLE_RESULTS):
        rc = run_dominance(args, out=out)
    assert rc == 0
    text = out.getvalue()
    assert "fast" in text
    assert "slow" in text


def test_run_dominance_json_output():
    p = build_dominance_parser()
    args = p.parse_args(["results.json", "--format", "json"])
    out = io.StringIO()
    with patch("batchmark.cli_dominance.load_results", return_value=SAMPLE_RESULTS):
        rc = run_dominance(args, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["winner"] == "fast"
    assert data[0]["loser"] == "slow"


def test_run_dominance_strict_only_filter():
    p = build_dominance_parser()
    args = p.parse_args(["results.json", "--strict-only"])
    out = io.StringIO()
    with patch("batchmark.cli_dominance.load_results", return_value=SAMPLE_RESULTS):
        rc = run_dominance(args, out=out)
    assert rc == 0
    assert "fast" in out.getvalue()
