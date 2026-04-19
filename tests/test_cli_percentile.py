import json
import io
import pytest
from unittest.mock import patch
from batchmark.runner import BenchmarkResult
from batchmark.cli_percentile import build_percentile_parser, run_percentile


def make_result(cmd="sort", size=50, elapsed=1.0, success=True):
    return BenchmarkResult(
        command=cmd, size=size, elapsed=elapsed,
        returncode=0 if success else 1, success=success, timed_out=False,
    )


def test_build_percentile_parser_defaults():
    p = build_percentile_parser()
    args = p.parse_args(["results.json"])
    assert args.history_file == "results.json"
    assert args.tag is None
    assert args.format == "table"


def test_build_percentile_parser_all_flags():
    p = build_percentile_parser()
    args = p.parse_args(["r.json", "--tag", "v1", "--format", "json"])
    assert args.tag == "v1"
    assert args.format == "json"


def test_run_percentile_table(tmp_path):
    results = [make_result(elapsed=float(i)) for i in range(1, 4)]
    hist = str(tmp_path / "h.json")
    with patch("batchmark.cli_percentile.load_results", return_value=results):
        args = build_percentile_parser().parse_args([hist])
        out = io.StringIO()
        run_percentile(args, out=out)
        text = out.getvalue()
    assert "sort" in text
    assert "p50" in text


def test_run_percentile_json(tmp_path):
    results = [make_result(elapsed=float(i)) for i in range(1, 4)]
    hist = str(tmp_path / "h.json")
    with patch("batchmark.cli_percentile.load_results", return_value=results):
        args = build_percentile_parser().parse_args([hist, "--format", "json"])
        out = io.StringIO()
        run_percentile(args, out=out)
        data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "sort"
    assert "p90" in data[0]


def test_run_percentile_empty(tmp_path):
    hist = str(tmp_path / "h.json")
    with patch("batchmark.cli_percentile.load_results", return_value=[]):
        args = build_percentile_parser().parse_args([hist])
        out = io.StringIO()
        run_percentile(args, out=out)
    assert "No data" in out.getvalue()
