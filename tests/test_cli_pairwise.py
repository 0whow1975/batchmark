"""Tests for batchmark.cli_pairwise."""
import io
import json
import pytest
from unittest.mock import patch
from batchmark.runner import BenchmarkResult
from batchmark.cli_pairwise import build_pairwise_parser, run_pairwise


def make_result(command, size, times, error=None):
    return BenchmarkResult(
        command=command,
        size=size,
        times=times,
        returncode=0 if error is None else 1,
        error=error,
    )


SAMPLE_RESULTS = [
    make_result("fast", 100, [0.5, 0.5]),
    make_result("fast", 200, [1.0, 1.0]),
    make_result("slow", 100, [1.5, 1.5]),
    make_result("slow", 200, [2.5, 2.5]),
]


def test_build_pairwise_parser_defaults():
    p = build_pairwise_parser()
    args = p.parse_args(["history.json", "cmd_a", "cmd_b"])
    assert args.history_file == "history.json"
    assert args.command_a == "cmd_a"
    assert args.command_b == "cmd_b"
    assert args.tag is None
    assert args.tie_threshold == pytest.approx(0.02)
    assert args.format == "table"


def test_build_pairwise_parser_all_flags():
    p = build_pairwise_parser()
    args = p.parse_args(
        ["h.json", "a", "b", "--tag", "v1", "--tie-threshold", "0.05", "--format", "json"]
    )
    assert args.tag == "v1"
    assert args.tie_threshold == pytest.approx(0.05)
    assert args.format == "json"


def test_run_pairwise_table_output():
    parser = build_pairwise_parser()
    args = parser.parse_args(["h.json", "fast", "slow"])
    out = io.StringIO()
    with patch("batchmark.cli_pairwise.load_results", return_value=SAMPLE_RESULTS):
        run_pairwise(args, out=out)
    text = out.getvalue()
    assert "fast" in text
    assert "slow" in text
    assert "Summary" in text


def test_run_pairwise_json_output():
    parser = build_pairwise_parser()
    args = parser.parse_args(["h.json", "fast", "slow", "--format", "json"])
    out = io.StringIO()
    with patch("batchmark.cli_pairwise.load_results", return_value=SAMPLE_RESULTS):
        run_pairwise(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["winner"] == "a"   # fast wins
    assert "ratio" in data[0]


def test_run_pairwise_no_shared_sizes():
    results = [
        make_result("cmd_a", 100, [1.0]),
        make_result("cmd_b", 999, [1.0]),
    ]
    parser = build_pairwise_parser()
    args = parser.parse_args(["h.json", "cmd_a", "cmd_b"])
    out = io.StringIO()
    with patch("batchmark.cli_pairwise.load_results", return_value=results):
        run_pairwise(args, out=out)
    assert "No pairwise data" in out.getvalue()
