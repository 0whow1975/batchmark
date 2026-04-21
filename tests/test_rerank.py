"""Tests for batchmark.rerank and batchmark.cli_rerank."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from batchmark.rerank import (
    RerankRow,
    rerank_results,
    render_rerank_table,
    VALID_METRICS,
)
from batchmark.cli_rerank import build_rerank_parser, run_rerankrom batchmark.runner import BenchmarkResult


def make_result(command, size, times, success=True):
    r = BenchmarkResult(command=command, size=size, times=times, success=success)
    return r


# ---------------------------------------------------------------------------
# rerank_results
# ---------------------------------------------------------------------------

def test_rerank_basicascending():
    results = [
        make_result("cmd_a", 100, [0.5, 0.6, 0.7]),cmd_b", 100, [0.2, 0.3, 0.4]),
        make_result("cmd_c", 100, [1.0, 1.1, 1.2]),
    ]
    rows = rerank_results(results, metric="meanassert [r.command for r in rows] == ["cmd_b", "cmd_a", "cmd_c"]
    assert rows[0].rank == 1
    assert rows[2].rank == 3


def test_rerank_descending():
    results = [
        make_result("fast", 10, [0.1, 0.2]),
        make_result("slow", 10, [1.0, 1.1]),
    ]
    rows = rerank_results(results, metric="mean", ascending=False)
    assert rows[0].command == "slow"
    assert rows[1].command == "fast"


def test_rerank_skips_failures():
    results = [
        make_result("ok", 50, [0.3, 0.4]),
        make_result("bad", 50, [], success=False),
    ]
    rows = rerank_results(results)
    assert len(rows) == 1
    assert rows[0].command == "ok"


def test_rerank_top_n():
    results = [make_result(f"cmd_{i}", 100, [float(i)]) for i in range(5)]
    rows = rerank_results(results, top_n=3)
    assert len(rows) == 3


def test_rerank_invalid_metric():
    with pytest.raises(ValueError, match="metric must be one of"):
        rerank_results([], metric="p99")


def test_rerank_empty():
    assert rerank_results([]) == []


def test_rerank_metric_min():
    results = [
        make_result("a", 10, [1.0, 2.0, 3.0]),
        make_result("b", 10, [0.5, 2.0, 3.0]),
    ]
    rows = rerank_results(results, metric="min")
    assert rows[0].command == "b"
    assert rows[0].value == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# render_rerank_table
# ---------------------------------------------------------------------------

def test_render_rerank_table_empty():
    assert render_rerank_table([]) == "No results to rank."


def test_render_rerank_table_contains_data():
    row = RerankRow(rank=1, command="mycmd", size=256, metric="mean", value=0.123, runs=5)
    output = render_rerank_table([row])
    assert "mycmd" in output
    assert "256" in output
    assert "0.1230" in output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_rerank_parser_defaults():
    parser = build_rerank_parser()
    args = parser.parse_args(["results.json"])
    assert args.metric == "mean"
    assert args.desc is False
    assert args.top is None
    assert args.fmt == "table"


def test_build_rerank_parser_all_flags():
    parser = build_rerank_parser()
    args = parser.parse_args(["r.json", "--metric", "min", "--desc", "--top", "5", "--format", "json"])
    assert args.metric == "min"
    assert args.desc is True
    assert args.top == 5
    assert args.fmt == "json"


def test_run_rerank_table_output():
    results = [make_result("echo", 100, [0.1, 0.2, 0.3])]
    parser = build_rerank_parser()
    args = parser.parse_args(["dummy.json", "--metric", "mean"])
    out = StringIO()
    with patch("batchmark.cli_rerank.load_results", return_value=results):
        run_rerank(args, out=out)
    assert "echo" in out.getvalue()


def test_run_rerank_json_output():
    results = [make_result("sort", 200, [0.4, 0.5])]
    parser = build_rerank_parser()
    args = parser.parse_args(["dummy.json", "--format", "json"])
    out = StringIO()
    with patch("batchmark.cli_rerank.load_results", return_value=results):
        run_rerank(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "sort"
    assert "rank" in data[0]
