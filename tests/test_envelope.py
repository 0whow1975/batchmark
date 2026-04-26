"""Tests for batchmark.envelope."""
from __future__ import annotations

import pytest
from batchmark.envelope import build_envelope, render_envelope_table, EnvelopeResult
from batchmark.runner import BenchmarkResult


def make_result(command="cmd", size=100, mean=1.0, success=True) -> BenchmarkResult:
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
        exit_code=0 if success else 1,
    )


def test_build_envelope_basic():
    results = [
        make_result(mean=1.0),
        make_result(mean=2.0),
        make_result(mean=1.5),
    ]
    env = build_envelope(results)
    assert ("cmd", 100) in env
    e = env[("cmd", 100)]
    assert e.lo == pytest.approx(1.0)
    assert e.hi == pytest.approx(2.0)
    assert e.spread == pytest.approx(1.0)
    assert e.spread_pct == pytest.approx(100.0)


def test_build_envelope_skips_failures():
    results = [
        make_result(mean=1.0),
        make_result(mean=5.0, success=False),
    ]
    env = build_envelope(results)
    e = env[("cmd", 100)]
    assert e.lo == pytest.approx(1.0)
    assert e.hi == pytest.approx(1.0)


def test_build_envelope_empty():
    env = build_envelope([])
    assert env == {}


def test_build_envelope_command_filter():
    results = [
        make_result(command="a", mean=1.0),
        make_result(command="b", mean=9.0),
    ]
    env = build_envelope(results, command_filter="a")
    assert ("a", 100) in env
    assert ("b", 100) not in env


def test_build_envelope_multiple_sizes():
    results = [
        make_result(size=100, mean=1.0),
        make_result(size=200, mean=2.0),
        make_result(size=100, mean=3.0),
    ]
    env = build_envelope(results)
    assert env[("cmd", 100)].hi == pytest.approx(3.0)
    assert env[("cmd", 200)].lo == pytest.approx(2.0)


def test_render_envelope_table_empty():
    out = render_envelope_table({})
    assert "No envelope data" in out


def test_render_envelope_table_contains_columns():
    results = [make_result(mean=1.0), make_result(mean=2.0)]
    env = build_envelope(results)
    table = render_envelope_table(env)
    assert "Command" in table
    assert "Spread" in table
    assert "cmd" in table
    assert "100" in table
