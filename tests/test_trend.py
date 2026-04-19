import pytest
from batchmark.runner import BenchmarkResult
from batchmark.trend import build_trend, render_trend_table, TrendPoint, TrendSeries


def make_result(command, size, times, success=True):
    return BenchmarkResult(command=command, size=size, times=times, success=success)


def test_build_trend_basic():
    results_by_tag = {
        "v1": [make_result("cmd_a", 100, [1.0, 1.2, 1.1])],
        "v2": [make_result("cmd_a", 100, [0.8, 0.9, 0.85])],
    }
    series = build_trend(results_by_tag)
    assert len(series) == 1
    assert series[0].command == "cmd_a"
    assert len(series[0].points) == 2


def test_build_trend_skips_failures():
    results_by_tag = {
        "v1": [make_result("cmd_a", 100, [], success=False)],
        "v2": [make_result("cmd_a", 100, [0.5, 0.6])],
    }
    series = build_trend(results_by_tag)
    assert len(series) == 1
    assert len(series[0].points) == 1
    assert series[0].points[0].tag == "v2"


def test_build_trend_empty():
    series = build_trend({})
    assert series == []


def test_trend_series_improving():
    s = TrendSeries(
        command="cmd",
        points=[
            TrendPoint(tag="v1", size=100, mean=2.0, median=2.0),
            TrendPoint(tag="v2", size=100, mean=1.0, median=1.0),
        ],
    )
    assert s.improving is True


def test_trend_series_not_improving():
    s = TrendSeries(
        command="cmd",
        points=[
            TrendPoint(tag="v1", size=100, mean=1.0, median=1.0),
            TrendPoint(tag="v2", size=100, mean=2.0, median=2.0),
        ],
    )
    assert s.improving is False


def test_trend_series_single_point():
    s = TrendSeries(
        command="cmd",
        points=[TrendPoint(tag="v1", size=100, mean=1.0, median=1.0)],
    )
    assert s.improving is None


def test_render_trend_table_empty():
    result = render_trend_table([])
    assert "No trend data" in result


def test_render_trend_table_basic():
    results_by_tag = {
        "v1": [make_result("echo", 50, [0.1, 0.2])],
        "v2": [make_result("echo", 50, [0.05, 0.07])],
    }
    series = build_trend(results_by_tag)
    table = render_trend_table(series)
    assert "echo" in table
    assert "v1" in table
    assert "v2" in table
