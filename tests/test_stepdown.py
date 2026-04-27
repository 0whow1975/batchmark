"""Tests for batchmark.stepdown and batchmark.cli_stepdown."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.stepdown import detect_stepdowns, render_stepdown_table
from batchmark.cli_stepdown import build_stepdown_parser, run_stepdown


def make_result(cmd, size, mean, failed=False):
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=[] if failed else [mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        failed=failed,
    )


# ---------------------------------------------------------------------------
# detect_stepdowns
# ---------------------------------------------------------------------------

def test_detect_stepdowns_basic():
    results = [
        make_result("cmd", 100, 2.0),
        make_result("cmd", 200, 2.1),
        make_result("cmd", 400, 1.0),   # big drop — should be flagged
        make_result("cmd", 800, 0.95),
    ]
    points = detect_stepdowns(results, threshold=0.20)
    assert len(points) == 1
    p = points[0]
    assert p.size_before == 200
    assert p.size_after == 400
    assert p.drop_pct == pytest.approx((1 - 1.0 / 2.1) * 100, rel=1e-3)


def test_detect_stepdowns_no_stepdown():
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 1.1),
        make_result("cmd", 400, 1.2),
    ]
    assert detect_stepdowns(results, threshold=0.20) == []


def test_detect_stepdowns_skips_failures():
    results = [
        make_result("cmd", 100, 2.0, failed=True),
        make_result("cmd", 200, 0.5),
    ]
    # Only one valid result — no pair to compare.
    assert detect_stepdowns(results, threshold=0.10) == []


def test_detect_stepdowns_command_filter():
    results = [
        make_result("fast", 100, 2.0),
        make_result("fast", 200, 1.0),  # 50% drop
        make_result("slow", 100, 2.0),
        make_result("slow", 200, 1.0),  # 50% drop
    ]
    points = detect_stepdowns(results, threshold=0.20, command="fast")
    assert all(p.command == "fast" for p in points)
    assert len(points) == 1


def test_detect_stepdowns_threshold_boundary():
    # Exactly at threshold — should NOT be flagged (ratio == 1 - threshold)
    results = [
        make_result("cmd", 100, 1.0),
        make_result("cmd", 200, 0.80),  # exactly 20% drop
    ]
    # ratio = 0.80, threshold = 0.20 → ratio < 0.80 is False
    assert detect_stepdowns(results, threshold=0.20) == []


# ---------------------------------------------------------------------------
# render_stepdown_table
# ---------------------------------------------------------------------------

def test_render_stepdown_table_empty():
    assert render_stepdown_table([]) == "No step-down points detected."


def test_render_stepdown_table_contains_fields():
    results = [
        make_result("mycommand", 100, 3.0),
        make_result("mycommand", 200, 1.0),
    ]
    points = detect_stepdowns(results, threshold=0.20)
    table = render_stepdown_table(points)
    assert "mycommand" in table
    assert "100" in table
    assert "200" in table


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_build_stepdown_parser_defaults():
    p = build_stepdown_parser()
    args = p.parse_args(["history.json"])
    assert args.threshold == 0.20
    assert args.command is None
    assert args.tag is None
    assert args.fmt == "table"


def test_run_stepdown_table_output():
    results = [
        make_result("cmd", 100, 2.0),
        make_result("cmd", 200, 1.0),
    ]
    parser = build_stepdown_parser()
    args = parser.parse_args(["dummy.json", "--threshold", "0.20"])
    out = StringIO()
    with patch("batchmark.cli_stepdown.load_results", return_value=results):
        run_stepdown(args, out=out)
    assert "cmd" in out.getvalue()


def test_run_stepdown_json_output():
    results = [
        make_result("cmd", 100, 2.0),
        make_result("cmd", 200, 1.0),
    ]
    parser = build_stepdown_parser()
    args = parser.parse_args(["dummy.json", "--format", "json"])
    out = StringIO()
    with patch("batchmark.cli_stepdown.load_results", return_value=results):
        run_stepdown(args, out=out)
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"
    assert "drop_pct" in data[0]
