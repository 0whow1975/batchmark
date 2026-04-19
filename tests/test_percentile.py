import pytest
from batchmark.runner import BenchmarkResult
from batchmark.percentile import (
    _percentile,
    compute_percentiles,
    render_percentile_table,
)


def make_result(cmd="echo", size=100, elapsed=1.0, success=True):
    return BenchmarkResult(
        command=cmd, size=size, elapsed=elapsed,
        returncode=0 if success else 1, success=success, timed_out=False,
    )


def test_percentile_basic():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile(data, 50) == 3.0
    assert _percentile(data, 0) == 1.0
    assert _percentile(data, 100) == 5.0


def test_percentile_single():
    assert _percentile([7.0], 99) == 7.0


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        _percentile([], 50)


def test_compute_percentiles_basic():
    results = [make_result(elapsed=float(i)) for i in range(1, 6)]
    stats = compute_percentiles(results)
    assert len(stats) == 1
    s = stats[0]
    assert s.command == "echo"
    assert s.size == 100
    assert s.sample_count == 5
    assert s.p50 == pytest.approx(3.0)
    assert s.p99 > s.p90


def test_compute_percentiles_skips_failures():
    results = [
        make_result(elapsed=1.0),
        make_result(elapsed=2.0, success=False),
        make_result(elapsed=3.0),
    ]
    stats = compute_percentiles(results)
    assert stats[0].sample_count == 2


def test_compute_percentiles_multiple_commands():
    results = [
        make_result(cmd="a", size=10, elapsed=1.0),
        make_result(cmd="b", size=10, elapsed=2.0),
        make_result(cmd="a", size=10, elapsed=1.5),
    ]
    stats = compute_percentiles(results)
    cmds = [s.command for s in stats]
    assert "a" in cmds and "b" in cmds


def test_compute_percentiles_empty():
    assert compute_percentiles([]) == []


def test_render_percentile_table_empty():
    assert render_percentile_table([]) == "No data."


def test_render_percentile_table_basic():
    results = [make_result(elapsed=float(i)) for i in range(1, 6)]
    stats = compute_percentiles(results)
    table = render_percentile_table(stats)
    assert "p50" in table
    assert "p99" in table
    assert "echo" in table
