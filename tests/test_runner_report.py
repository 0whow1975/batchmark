import pytest
from unittest.mock import patch, MagicMock
from batchmark.runner import run_benchmark, BenchmarkResult
from batchmark.report import result_to_dict, render_json, render_table


def make_mock_proc(returncode=0):
    proc = MagicMock()
    proc.returncode = returncode
    return proc


@patch("batchmark.runner.subprocess.run")
def test_run_benchmark_basic(mock_run):
    mock_run.return_value = make_mock_proc(0)
    result = run_benchmark("echo hello", input_size=100, runs=3)
    assert result.runs == 3
    assert len(result.times) == 3
    assert all(t >= 0 for t in result.times)
    assert result.success_rate == 1.0
    assert result.error is None


@patch("batchmark.runner.subprocess.run")
def test_run_benchmark_failure(mock_run):
    mock_run.return_value = make_mock_proc(1)
    result = run_benchmark("false", input_size=0, runs=2)
    assert result.success_rate == 0.0


@patch("batchmark.runner.subprocess.run")
def test_run_benchmark_timeout(mock_run):
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=1)
    result = run_benchmark("sleep 100", input_size=0, runs=3, timeout=1)
    assert result.error is not None
    assert "timed out" in result.error


def test_result_stats():
    r = BenchmarkResult(command="cmd", input_size=10, runs=3, times=[1.0, 2.0, 3.0], exit_codes=[0, 0, 0])
    assert r.mean == pytest.approx(2.0)
    assert r.min == 1.0
    assert r.max == 3.0
    assert r.success_rate == 1.0


def test_result_to_dict():
    r = BenchmarkResult(command="ls", input_size=50, runs=2, times=[0.1, 0.2], exit_codes=[0, 0])
    d = result_to_dict(r)
    assert d["command"] == "ls"
    assert d["input_size"] == 50
    assert "mean_s" in d


def test_render_json():
    r = BenchmarkResult(command="ls", input_size=50, runs=2, times=[0.1, 0.2], exit_codes=[0, 0])
    out = render_json([r])
    assert "ls" in out
    assert "mean_s" in out


def test_render_table():
    r = BenchmarkResult(command="ls", input_size=50, runs=2, times=[0.1, 0.2], exit_codes=[0, 0])
    table = render_table([r])
    assert "command" in table
    assert "ls" in table
    assert "input_size" in table
