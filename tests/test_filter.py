import pytest
from batchmark.runner import BenchmarkResult
from batchmark.filter import (
    filter_results,
    group_by_command,
    group_by_size,
    top_n,
)


def make_result(command="cmd", input_size=100, times=None, success=True, exit_code=0):
    return BenchmarkResult(
        command=command,
        input_size=input_size,
        times=times or [0.1, 0.2, 0.3],
        success=success,
        exit_code=exit_code,
        timed_out=False,
    )


def test_filter_by_command():
    results = [make_result("a"), make_result("b"), make_result("a")]
    assert len(filter_results(results, command="a")) == 2


def test_filter_by_size_range():
    results = [make_result(input_size=s) for s in [10, 50, 100, 200]]
    filtered = filter_results(results, min_size=50, max_size=100)
    sizes = [r.input_size for r in filtered]
    assert sizes == [50, 100]


def test_filter_success_only():
    results = [make_result(success=True), make_result(success=False)]
    assert len(filter_results(results, success_only=True)) == 1


def test_filter_predicate():
    results = [make_result(input_size=s) for s in [10, 20, 30]]
    filtered = filter_results(results, predicate=lambda r: r.input_size > 15)
    assert len(filtered) == 2


def test_group_by_command():
    results = [make_result("x"), make_result("y"), make_result("x")]
    groups = group_by_command(results)
    assert set(groups.keys()) == {"x", "y"}
    assert len(groups["x"]) == 2


def test_group_by_size():
    results = [make_result(input_size=s) for s in [1, 2, 1, 3]]
    groups = group_by_size(results)
    assert len(groups[1]) == 2
    assert len(groups[2]) == 1


def test_top_n_mean():
    r1 = make_result("slow", times=[1.0, 1.0])
    r2 = make_result("fast", times=[0.1, 0.1])
    result = top_n([r1, r2], n=1, key="mean")
    assert result[0].command == "fast"


def test_top_n_invalid_key():
    with pytest.raises(ValueError):
        top_n([make_result()], n=1, key="invalid")


def test_top_n_skips_failures():
    results = [make_result(success=False), make_result("ok", times=[0.5])]
    result = top_n(results, n=5, key="min")
    assert len(result) == 1
    assert result[0].command == "ok"
