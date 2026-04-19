"""Tests for batchmark.export module."""

import pytest
from batchmark.runner import BenchmarkResult
from batchmark.export import render_csv, render_markdown


def make_result(label="cmd", size=100, times=None, success=True):
    times = times or [0.1, 0.2, 0.15]
    return BenchmarkResult(label=label, size=size, times=times, success=success)


def test_render_csv_empty():
    assert render_csv([]) == ""


def test_render_csv_basic():
    result = make_result(label="sort", size=500, times=[0.1, 0.2, 0.3])
    output = render_csv([result])
    lines = output.strip().splitlines()
    assert lines[0].startswith("label,size")
    assert "sort" in lines[1]
    assert "500" in lines[1]


def test_render_csv_multiple():
    results = [make_result(size=s) for s in [10, 100, 1000]]
    output = render_csv(results)
    lines = output.strip().splitlines()
    assert len(lines) == 4  # header + 3 data rows


def test_render_csv_failure_row():
    result = make_result(success=False, times=[])
    output = render_csv([result])
    assert "False" in output or "false" in output.lower() or "no" in output.lower() or output


def test_render_markdown_empty():
    assert render_markdown([]) == ""


def test_render_markdown_basic():
    result = make_result(label="grep", size=200, times=[0.05, 0.06, 0.07])
    output = render_markdown([result])
    assert "| Label |" in output
    assert "grep" in output
    assert "200" in output
    assert "---" in output


def test_render_markdown_ok_column():
    good = make_result(success=True)
    bad = make_result(success=False, times=[])
    output = render_markdown([good, bad])
    assert "yes" in output
    assert "no" in output


def test_render_markdown_multiple_rows():
    results = [make_result(label=f"cmd{i}", size=i * 10) for i in range(1, 4)]
    output = render_markdown(results)
    for i in range(1, 4):
        assert f"cmd{i}" in output
