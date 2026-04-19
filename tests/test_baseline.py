"""Tests for batchmark.baseline module."""

import json
import os
import tempfile
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.baseline import (
    set_baseline,
    load_baseline,
    diff_against_baseline,
    render_baseline_table,
)


def make_result(cmd="echo", size=100, mean=1.0, success=True):
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
        error=None,
    )


def test_set_and_load_baseline():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        results = [make_result("cmd1", 10, 0.5), make_result("cmd2", 20, 1.0)]
        set_baseline(results, path)
        loaded = load_baseline(path)
        assert len(loaded) == 2
        assert loaded[0].command == "cmd1"
    finally:
        os.unlink(path)


def test_diff_no_regression():
    baseline = [make_result("echo", 100, 1.0)]
    current = [make_result("echo", 100, 1.05)]
    diffs = diff_against_baseline(baseline, current, regression_threshold=0.10)
    assert len(diffs) == 1
    assert not diffs[0].regression
    assert abs(diffs[0].pct_change - 0.05) < 1e-6


def test_diff_regression_flagged():
    baseline = [make_result("echo", 100, 1.0)]
    current = [make_result("echo", 100, 1.5)]
    diffs = diff_against_baseline(baseline, current, regression_threshold=0.10)
    assert diffs[0].regression


def test_diff_skips_failures():
    baseline = [make_result("echo", 100, 1.0)]
    current = [make_result("echo", 100, 2.0, success=False)]
    diffs = diff_against_baseline(baseline, current)
    assert diffs == []


def test_diff_missing_baseline_key():
    baseline = [make_result("echo", 100, 1.0)]
    current = [make_result("echo", 200, 1.0)]
    diffs = diff_against_baseline(baseline, current)
    assert diffs == []


def test_render_baseline_table_empty():
    out = render_baseline_table([])
    assert "No comparable" in out


def test_render_baseline_table_basic():
    baseline = [make_result("sort", 50, 0.8)]
    current = [make_result("sort", 50, 1.0)]
    diffs = diff_against_baseline(baseline, current)
    table = render_baseline_table(diffs)
    assert "sort" in table
    assert "YES" in table
