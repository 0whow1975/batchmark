"""Tests for batchmark.normalize."""

import pytest
from batchmark.runner import BenchmarkResult
from batchmark.normalize import (
    NormalizedResult,
    normalize_results,
    render_normalize_table,
)


def make_result(command, size, times, error=None):
    return BenchmarkResult(command=command, size=size, times=times, error=error)


REF = "cmd_ref"
OTHER = "cmd_other"


def test_normalize_basic():
    results = [
        make_result(REF, 100, [1.0, 1.0, 1.0]),
        make_result(OTHER, 100, [2.0, 2.0, 2.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    other_rows = [r for r in rows if r.command == OTHER]
    assert len(other_rows) == 1
    row = other_rows[0]
    assert row.ratio == pytest.approx(2.0)
    assert row.pct_change == pytest.approx(100.0)
    assert row.faster is False


def test_normalize_faster_command():
    results = [
        make_result(REF, 100, [2.0, 2.0]),
        make_result(OTHER, 100, [1.0, 1.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    other_rows = [r for r in rows if r.command == OTHER]
    assert len(other_rows) == 1
    assert other_rows[0].faster is True
    assert other_rows[0].ratio == pytest.approx(0.5)
    assert other_rows[0].pct_change == pytest.approx(-50.0)


def test_normalize_skips_failures():
    results = [
        make_result(REF, 100, [], error="timeout"),
        make_result(OTHER, 100, [1.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    # Reference failed, so no ref time -> no rows
    assert rows == []


def test_normalize_skips_other_failures():
    results = [
        make_result(REF, 100, [1.0]),
        make_result(OTHER, 100, [], error="crash"),
    ]
    rows = normalize_results(results, reference_command=REF)
    other_rows = [r for r in rows if r.command == OTHER]
    assert other_rows == []


def test_normalize_multiple_sizes():
    results = [
        make_result(REF, 100, [1.0]),
        make_result(REF, 200, [2.0]),
        make_result(OTHER, 100, [1.5]),
        make_result(OTHER, 200, [3.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    by_size = {r.size: r for r in rows if r.command == OTHER}
    assert by_size[100].ratio == pytest.approx(1.5)
    assert by_size[200].ratio == pytest.approx(1.5)


def test_normalize_reference_included_in_output():
    results = [
        make_result(REF, 100, [1.0]),
        make_result(OTHER, 100, [1.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    ref_rows = [r for r in rows if r.command == REF]
    assert len(ref_rows) == 1
    assert ref_rows[0].ratio == pytest.approx(1.0)
    assert ref_rows[0].pct_change == pytest.approx(0.0)


def test_render_normalize_table_empty():
    output = render_normalize_table([], reference=REF)
    assert "No normalized" in output


def test_render_normalize_table_contains_data():
    results = [
        make_result(REF, 100, [1.0]),
        make_result(OTHER, 100, [2.0]),
    ]
    rows = normalize_results(results, reference_command=REF)
    output = render_normalize_table(rows, reference=REF)
    assert REF in output
    assert OTHER in output
    assert "100" in output
    assert "Reference command" in output
