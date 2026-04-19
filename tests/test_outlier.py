import pytest
from batchmark.runner import BenchmarkResult
from batchmark.outlier import detect_outliers, render_outlier_table


def make_result(command, size, times, success=True):
    return BenchmarkResult(
        command=command,
        size=size,
        times=times,
        exit_codes=[0] * len(times),
        success=success,
        error=None,
    )


def test_detect_outliers_basic():
    results = [
        make_result("cmd", 100, [1.0, 1.0, 1.0]),
        make_result("cmd", 200, [1.1, 1.0, 0.9]),
        make_result("cmd", 300, [10.0, 10.0, 10.0]),  # outlier
    ]
    annotated = detect_outliers(results, threshold=2.0)
    assert len(annotated) == 3
    assert annotated[2].is_outlier is True
    assert annotated[0].is_outlier is False


def test_detect_outliers_no_outliers():
    results = [
        make_result("cmd", 100, [1.0, 1.0]),
        make_result("cmd", 200, [1.1, 1.1]),
        make_result("cmd", 300, [1.2, 1.2]),
    ]
    annotated = detect_outliers(results, threshold=2.0)
    assert all(not o.is_outlier for o in annotated)


def test_detect_outliers_too_few():
    results = [make_result("cmd", 100, [1.0, 1.0])]
    annotated = detect_outliers(results, threshold=2.0)
    assert annotated[0].z_score == 0.0
    assert annotated[0].is_outlier is False


def test_detect_outliers_skips_failures():
    results = [
        make_result("cmd", 100, [], success=False),
        make_result("cmd", 200, [1.0, 1.0]),
        make_result("cmd", 300, [1.1, 1.1]),
    ]
    annotated = detect_outliers(results, threshold=2.0)
    assert annotated[0].is_outlier is False
    assert annotated[0].z_score == 0.0


def test_render_outlier_table_contains_header():
    results = [
        make_result("echo hello", 100, [0.5, 0.5]),
        make_result("echo hello", 200, [5.0, 5.0]),
    ]
    annotated = detect_outliers(results, threshold=1.0)
    table = render_outlier_table(annotated)
    assert "Command" in table
    assert "Z-Score" in table
    assert "echo hello" in table
