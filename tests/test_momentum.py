"""Tests for batchmark.momentum and batchmark.cli_momentum."""

from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace
from typing import List

import pytest

from batchmark.momentum import (
    MomentumResult,
    _trend_label,
    compute_momentum,
    render_momentum_table,
)
from batchmark.cli_momentum import run_momentum
from batchmark.runner import BenchmarkResult


def make_result(command: str, size: int, mean: float, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=command,
        size=size,
        times=[mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        success=success,
    )


# ---------------------------------------------------------------------------
# Unit tests for compute_momentum
# ---------------------------------------------------------------------------

def test_compute_momentum_basic():
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 3.0),
    ]
    rows = compute_momentum(results)
    assert len(rows) == 1
    r = rows[0]
    assert r.command == "cmd"
    assert r.positive_steps == 2
    assert r.negative_steps == 0
    assert r.momentum_score == pytest.approx(1.0)
    assert r.trend == "decelerating"


def test_compute_momentum_accelerating():
    results = [
        make_result("cmd", 10, 3.0),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 1.0),
    ]
    rows = compute_momentum(results)
    assert rows[0].momentum_score == pytest.approx(-1.0)
    assert rows[0].trend == "accelerating"


def test_compute_momentum_skips_failures():
    results = [
        make_result("cmd", 10, 1.0, success=False),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 3.0),
    ]
    rows = compute_momentum(results)
    # Only two successful points; still computes one delta
    assert len(rows) == 1
    assert rows[0].sizes == [20, 30]


def test_compute_momentum_too_few_points():
    results = [make_result("cmd", 10, 1.0)]
    assert compute_momentum(results) == []


def test_compute_momentum_command_filter():
    results = [
        make_result("a", 10, 1.0),
        make_result("a", 20, 2.0),
        make_result("b", 10, 0.5),
        make_result("b", 20, 1.5),
    ]
    rows = compute_momentum(results, command="a")
    assert len(rows) == 1
    assert rows[0].command == "a"


def test_trend_label_flat():
    assert _trend_label(0.0) == "flat"
    assert _trend_label(0.1) == "flat"


def test_trend_label_mixed():
    assert _trend_label(0.4) == "mixed"
    assert _trend_label(-0.4) == "mixed"


# ---------------------------------------------------------------------------
# render_momentum_table
# ---------------------------------------------------------------------------

def test_render_momentum_table_empty():
    assert "No momentum" in render_momentum_table([])


def test_render_momentum_table_contains_command():
    rows = compute_momentum([
        make_result("sort", 100, 0.1),
        make_result("sort", 200, 0.3),
    ])
    table = render_momentum_table(rows)
    assert "sort" in table
    assert "decelerating" in table


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _make_args(history_file, tag=None, command=None, fmt="table", min_score=None):
    return SimpleNamespace(
        history_file=history_file,
        tag=tag,
        command=command,
        fmt=fmt,
        min_score=min_score,
    )


def test_run_momentum_table_output(tmp_path):
    from batchmark.history import save_results
    results = [
        make_result("grep", 100, 0.2),
        make_result("grep", 200, 0.5),
        make_result("grep", 400, 1.1),
    ]
    path = str(tmp_path / "hist.json")
    save_results(results, path)
    out = StringIO()
    rc = run_momentum(_make_args(path), out=out)
    assert rc == 0
    assert "grep" in out.getvalue()


def test_run_momentum_json_output(tmp_path):
    from batchmark.history import save_results
    results = [
        make_result("awk", 50, 0.1),
        make_result("awk", 100, 0.2),
    ]
    path = str(tmp_path / "hist.json")
    save_results(results, path)
    out = StringIO()
    rc = run_momentum(_make_args(path, fmt="json"), out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "awk"
    assert "momentum_score" in data[0]


def test_run_momentum_min_score_filter(tmp_path):
    from batchmark.history import save_results
    # flat command (score ~0) and steep command (score 1.0)
    results = [
        make_result("flat", 10, 1.0),
        make_result("flat", 20, 1.0),
        make_result("steep", 10, 1.0),
        make_result("steep", 20, 2.0),
    ]
    path = str(tmp_path / "hist.json")
    save_results(results, path)
    out = StringIO()
    run_momentum(_make_args(path, min_score=0.5), out=out)
    text = out.getvalue()
    assert "steep" in text
    assert "flat" not in text
