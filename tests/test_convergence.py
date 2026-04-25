"""Tests for batchmark.convergence."""
from __future__ import annotations
import json
import io
from unittest.mock import patch

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.convergence import detect_convergence, render_convergence_table
from batchmark.cli_convergence import build_convergence_parser, run_convergence


def make_result(cmd, size, mean, success=True):
    return BenchmarkResult(
        command=cmd,
        size=size,
        runs=[mean] * 5,
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        success=success,
    )


def test_detect_convergence_basic():
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 1.1),
        make_result("cmd", 30, 1.05),
        make_result("cmd", 40, 1.02),
        make_result("cmd", 50, 1.03),
        make_result("cmd", 60, 1.01),
    ]
    rows = detect_convergence(results, window=3, threshold_pct=10.0)
    assert len(rows) == 1
    assert rows[0].command == "cmd"
    assert rows[0].converged is True
    assert rows[0].delta_pct is not None


def test_detect_convergence_no_convergence():
    results = [
        make_result("slow", 10, 1.0),
        make_result("slow", 20, 2.0),
        make_result("slow", 30, 4.0),
        make_result("slow", 40, 8.0),
        make_result("slow", 50, 16.0),
        make_result("slow", 60, 32.0),
    ]
    rows = detect_convergence(results, window=3, threshold_pct=5.0)
    assert rows[0].converged is False


def test_detect_convergence_skips_failures():
    results = [
        make_result("cmd", 10, 1.0, success=False),
        make_result("cmd", 20, 1.0, success=False),
    ]
    rows = detect_convergence(results)
    assert rows == []


def test_detect_convergence_too_few_points():
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 1.1),
    ]
    rows = detect_convergence(results, window=3)
    assert rows[0].converged is False
    assert rows[0].delta_pct is None


def test_render_convergence_table_empty():
    assert render_convergence_table([]) == "No convergence data."


def test_render_convergence_table_contains_command():
    results = [make_result("mycommand", i * 10, 1.0) for i in range(1, 8)]
    rows = detect_convergence(results, window=3)
    table = render_convergence_table(rows)
    assert "mycommand" in table
    assert "yes" in table or "no" in table


def test_run_convergence_table(tmp_path):
    import json as _json
    from batchmark.history import save_results
    hist = tmp_path / "hist.json"
    results = [make_result("cmd", i * 10, 1.0 + i * 0.01) for i in range(1, 8)]
    save_results(str(hist), results)
    args = build_convergence_parser().parse_args([str(hist), "--window", "3", "--threshold", "50"])
    buf = io.StringIO()
    run_convergence(args, out=buf)
    assert "cmd" in buf.getvalue()


def test_run_convergence_json(tmp_path):
    from batchmark.history import save_results
    hist = tmp_path / "hist.json"
    results = [make_result("cmd", i * 10, 1.0) for i in range(1, 8)]
    save_results(str(hist), results)
    args = build_convergence_parser().parse_args([str(hist), "--format", "json"])
    buf = io.StringIO()
    run_convergence(args, out=buf)
    data = json.loads(buf.getvalue())
    assert isinstance(data, list)
    assert data[0]["command"] == "cmd"
