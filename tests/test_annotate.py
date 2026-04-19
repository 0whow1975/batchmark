"""Tests for batchmark.annotate module."""

import pytest
from batchmark.runner import BenchmarkResult
from batchmark.annotate import (
    AnnotatedResult,
    annotate_results,
    group_by_label,
    render_annotated_table,
)


def make_result(command="echo hi", size=100, mean=1.0, success=True):
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


def test_annotate_results_basic():
    results = [make_result(), make_result(size=200)]
    annotated = annotate_results(results, label="run-A", notes="first run", tags=["fast"])
    assert len(annotated) == 2
    for ar in annotated:
        assert ar.label == "run-A"
        assert ar.notes == "first run"
        assert ar.tags == ["fast"]


def test_annotate_results_defaults():
    results = [make_result()]
    annotated = annotate_results(results)
    assert annotated[0].label is None
    assert annotated[0].notes == ""
    assert annotated[0].tags == []


def test_annotate_results_empty():
    assert annotate_results([]) == []


def test_annotate_results_preserves_result():
    """Ensure annotated results retain a reference to the original BenchmarkResult."""
    r = make_result(command="ls", size=42, mean=3.14)
    annotated = annotate_results([r], label="check")
    assert annotated[0].result is r


def test_group_by_label():
    r1 = make_result(size=100)
    r2 = make_result(size=200)
    r3 = make_result(size=300)
    annotated = [
        AnnotatedResult(result=r1, label="A"),
        AnnotatedResult(result=r2, label="B"),
        AnnotatedResult(result=r3, label="A"),
    ]
    groups = group_by_label(annotated)
    assert set(groups.keys()) == {"A", "B"}
    assert len(groups["A"]) == 2
    assert len(groups["B"]) == 1


def test_group_by_label_none():
    r = make_result()
    annotated = [AnnotatedResult(result=r)]
    groups = group_by_label(annotated)
    assert None in groups


def test_render_annotated_table_basic():
    results = [make_result(command="sort", size=500, mean=2.5)]
    annotated = annotate_results(results, label="baseline", tags=["v1"])
    table = render_annotated_table(annotated)
    assert "baseline" in table
    assert "sort" in table
    assert "2.5000" in table
    assert "v1" in table


def test_render_annotated_table_empty():
    assert render_annotated_table([]) == "No annotated results."
