"""Tests for batchmark.plateau and batchmark.cli_plateau."""

import json
import pytest
from unittest.mock import patch
from batchmark.runner import BenchmarkResult
from batchmark.plateau import detect_plateaus, render_plateau_table, PlateauRegion
from batchmark.cli_plateau import build_plateau_parser, run_plateau


def make_result(command, size, times, success=True):
    return BenchmarkResult(
        command=command,
        size=size,
        times=times,
        exit_code=0 if success else 1,
        success=success,
    )


def test_detect_plateaus_basic():
    results = [
        make_result("cmd", 100, [1.0, 1.01, 0.99]),
        make_result("cmd", 200, [1.02, 0.98, 1.0]),
        make_result("cmd", 300, [1.01, 1.0, 0.99]),
        make_result("cmd", 400, [1.0, 1.01, 1.02]),
    ]
    regions = detect_plateaus(results, threshold_pct=5.0, min_points=3)
    assert len(regions) == 1
    assert regions[0].command == "cmd"
    assert regions[0].start_size == 100
    assert regions[0].end_size == 400
    assert regions[0].is_plateau is True


def test_detect_plateaus_no_plateau():
    results = [
        make_result("cmd", 100, [1.0]),
        make_result("cmd", 200, [2.0]),
        make_result("cmd", 300, [4.0]),
    ]
    regions = detect_plateaus(results, threshold_pct=5.0, min_points=3)
    assert regions == []


def test_detect_plateaus_skips_failures():
    results = [
        make_result("cmd", 100, [1.0, 1.0], success=False),
        make_result("cmd", 200, [1.0, 1.0]),
        make_result("cmd", 300, [1.0, 1.0]),
        make_result("cmd", 400, [1.0, 1.0]),
    ]
    regions = detect_plateaus(results, threshold_pct=5.0, min_points=3)
    assert len(regions) == 1
    assert regions[0].start_size == 200


def test_detect_plateaus_too_few_points():
    results = [
        make_result("cmd", 100, [1.0]),
        make_result("cmd", 200, [1.0]),
    ]
    regions = detect_plateaus(results, threshold_pct=5.0, min_points=3)
    assert regions == []


def test_render_plateau_table_empty():
    output = render_plateau_table([])
    assert "No plateau" in output


def test_render_plateau_table_basic():
    regions = [
        PlateauRegion(
            command="echo test",
            start_size=100,
            end_size=400,
            avg_time=1.005,
            variance_pct=1.23,
            is_plateau=True,
        )
    ]
    output = render_plateau_table(regions)
    assert "echo test" in output
    assert "100" in output
    assert "400" in output


def test_run_plateau_json_output(capsys):
    results = [
        make_result("cmd", 100, [1.0, 1.0]),
        make_result("cmd", 200, [1.0, 1.0]),
        make_result("cmd", 300, [1.0, 1.0]),
    ]
    parser = build_plateau_parser()
    args = parser.parse_args(["dummy.json", "--format", "json", "--threshold", "5"])
    with patch("batchmark.cli_plateau.load_results", return_value=results):
        run_plateau(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    if data:
        assert "command" in data[0]
        assert "start_size" in data[0]


def test_run_plateau_table_output(capsys):
    results = [
        make_result("cmd", 10, [2.0, 2.1]),
        make_result("cmd", 20, [2.05, 2.0]),
        make_result("cmd", 30, [2.02, 2.03]),
    ]
    parser = build_plateau_parser()
    args = parser.parse_args(["dummy.json", "--format", "table"])
    with patch("batchmark.cli_plateau.load_results", return_value=results):
        run_plateau(args)
    captured = capsys.readouterr()
    assert isinstance(captured.out, str)
