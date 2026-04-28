"""Tests for batchmark.cli_cadence."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from batchmark.runner import BenchmarkResult
from batchmark.cli_cadence import build_cadence_parser, run_cadence


def make_result(cmd: str, size: int, mean: float, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=[mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        success=success,
    )


RESULTS = [
    make_result("cmd", 100, 1.0),
    make_result("cmd", 200, 2.0),
    make_result("cmd", 400, 4.0),
]


def test_build_cadence_parser_defaults():
    parser = build_cadence_parser()
    args = parser.parse_args(["history.json"])
    assert args.history_file == "history.json"
    assert args.command is None
    assert args.tag is None
    assert args.format == "table"


def test_build_cadence_parser_all_flags():
    parser = build_cadence_parser()
    args = parser.parse_args([
        "history.json", "--command", "cmd", "--tag", "v1", "--format", "json"
    ])
    assert args.command == "cmd"
    assert args.tag == "v1"
    assert args.format == "json"


def test_run_cadence_table_output():
    parser = build_cadence_parser()
    args = parser.parse_args(["history.json"])
    out = io.StringIO()
    with patch("batchmark.cli_cadence.load_results", return_value=RESULTS):
        rc = run_cadence(args, out=out)
    assert rc == 0
    assert "cmd" in out.getvalue()
    assert "steady" in out.getvalue()


def test_run_cadence_json_output():
    parser = build_cadence_parser()
    args = parser.parse_args(["history.json", "--format", "json"])
    out = io.StringIO()
    with patch("batchmark.cli_cadence.load_results", return_value=RESULTS):
        rc = run_cadence(args, out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"
    assert "cv" in data[0]
    assert "label" in data[0]


def test_run_cadence_empty_results():
    parser = build_cadence_parser()
    args = parser.parse_args(["history.json"])
    out = io.StringIO()
    with patch("batchmark.cli_cadence.load_results", return_value=[]):
        rc = run_cadence(args, out=out)
    assert rc == 0
    assert "No cadence" in out.getvalue()
