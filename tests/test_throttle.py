"""Tests for batchmark.throttle."""

from __future__ import annotations

from typing import List

import pytest

from batchmark.runner import BenchmarkResult
from batchmark.throttle import ThrottleResult, detect_throttle, render_throttle_table


def make_result(
    command: str = "cmd",
    size: int = 100,
    elapsed: float = 1.0,
    success: bool = True,
) -> BenchmarkResult:
    return BenchmarkResult(
        command=command,
        size=size,
        elapsed=elapsed,
        returncode=0 if success else 1,
        success=success,
        timings=[elapsed],
    )


def test_detect_throttle_no_superlinear():
    results = [
        make_result(size=100, elapsed=1.0),
        make_result(size=200, elapsed=2.0),  # exact linear
        make_result(size=400, elapsed=4.0),
    ]
    rows = detect_throttle(results, threshold=1.2)
    assert all(not r.superlinear for r in rows)


def test_detect_throttle_flags_superlinear():
    results = [
        make_result(size=100, elapsed=1.0),
        make_result(size=200, elapsed=5.0),  # time_ratio=5, size_ratio=2 => 2.5 > 1.2
    ]
    rows = detect_throttle(results, threshold=1.2)
    flagged = [r for r in rows if r.superlinear]
    assert len(flagged) == 1
    assert flagged[0].size == 200


def test_detect_throttle_first_point_no_ratio():
    results = [make_result(size=100, elapsed=1.0)]
    rows = detect_throttle(results)
    assert rows[0].ratio is None
    assert not rows[0].superlinear


def test_detect_throttle_skips_failures():
    results = [
        make_result(size=100, elapsed=1.0, success=False),
        make_result(size=200, elapsed=10.0, success=False),
    ]
    rows = detect_throttle(results)
    assert rows == []


def test_detect_throttle_multiple_commands():
    results = [
        make_result(command="fast", size=100, elapsed=1.0),
        make_result(command="fast", size=200, elapsed=2.1),
        make_result(command="slow", size=100, elapsed=1.0),
        make_result(command="slow", size=200, elapsed=8.0),
    ]
    rows = detect_throttle(results, threshold=1.2)
    by_cmd = {r.command: r for r in rows if r.ratio is not None}
    assert not by_cmd["fast"].superlinear
    assert by_cmd["slow"].superlinear


def test_render_throttle_table_empty():
    assert render_throttle_table([]) == "No throttle data."


def test_render_throttle_table_contains_flag():
    results = [
        make_result(size=100, elapsed=1.0),
        make_result(size=200, elapsed=6.0),
    ]
    rows = detect_throttle(results, threshold=1.2)
    table = render_throttle_table(rows)
    assert "SLOW" in table
    assert "cmd" in table
