"""Tests for batchmark.saturation."""
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.saturation import detect_saturation, render_saturation_table, SaturationResult


def make_result(cmd: str, size: int, mean_time: float, success: bool = True) -> BenchmarkResult:
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=[mean_time],
        success=success,
        error=None,
    )


def test_detect_saturation_basic():
    # Growth slows sharply in second half -> saturated
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 3.0),
        make_result("cmd", 30, 3.2),
        make_result("cmd", 40, 3.3),
    ]
    out = detect_saturation(results, threshold=0.5)
    assert len(out) == 1
    assert out[0].saturated is True
    assert out[0].saturation_size == 30


def test_detect_saturation_no_saturation():
    # Steady linear growth -> not saturated
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 3.0),
        make_result("cmd", 40, 4.0),
    ]
    out = detect_saturation(results, threshold=0.5)
    assert len(out) == 1
    assert out[0].saturated is False
    assert out[0].saturation_size is None


def test_detect_saturation_skips_failures():
    results = [
        make_result("cmd", 10, 1.0, success=False),
        make_result("cmd", 20, 2.0, success=False),
        make_result("cmd", 30, 3.0),
        make_result("cmd", 40, 4.0),
    ]
    # Only 2 successful points -> below min_points=4, so no output
    out = detect_saturation(results, threshold=0.5, min_points=4)
    assert out == []


def test_detect_saturation_too_few_points():
    results = [
        make_result("cmd", 10, 1.0),
        make_result("cmd", 20, 2.0),
        make_result("cmd", 30, 3.0),
    ]
    out = detect_saturation(results, threshold=0.5, min_points=4)
    assert out == []


def test_detect_saturation_multiple_commands():
    results = [
        make_result("fast", 10, 1.0),
        make_result("fast", 20, 1.1),
        make_result("fast", 30, 1.15),
        make_result("fast", 40, 1.2),
        make_result("slow", 10, 1.0),
        make_result("slow", 20, 2.0),
        make_result("slow", 30, 3.0),
        make_result("slow", 40, 4.0),
    ]
    out = detect_saturation(results, threshold=0.5)
    by_cmd = {r.command: r for r in out}
    assert by_cmd["fast"].saturated is True
    assert by_cmd["slow"].saturated is False


def test_render_saturation_table_empty():
    assert render_saturation_table([]) == "No saturation data."


def test_render_saturation_table_contains_command():
    row = SaturationResult(
        command="mycommand",
        saturation_size=50,
        pre_slope=0.2,
        post_slope=0.05,
        ratio=0.25,
        saturated=True,
    )
    table = render_saturation_table([row])
    assert "mycommand" in table
    assert "50" in table
    assert "YES" in table
