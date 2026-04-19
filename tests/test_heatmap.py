import math
import pytest
from batchmark.runner import BenchmarkResult
from batchmark.heatmap import build_heatmap, render_heatmap_table, HeatmapCell


def make_result(cmd, size, mean_time, success=True):
    return BenchmarkResult(
        command=cmd,
        size=size,
        times=[mean_time],
        mean_time=mean_time,
        median_time=mean_time,
        stdev_time=0.0,
        min_time=mean_time,
        max_time=mean_time,
        success=success,
        exit_code=0 if success else 1,
    )


def test_build_heatmap_basic():
    results = [
        make_result("cmd_a", 10, 1.0),
        make_result("cmd_a", 20, 2.0),
        make_result("cmd_b", 10, 0.5),
        make_result("cmd_b", 20, 1.5),
    ]
    commands, sizes, grid = build_heatmap(results)
    assert commands == ["cmd_a", "cmd_b"]
    assert sizes == [10, 20]
    assert len(grid) == 2
    assert len(grid[0]) == 2


def test_build_heatmap_empty():
    commands, sizes, grid = build_heatmap([])
    assert commands == []
    assert sizes == []
    assert grid == []


def test_build_heatmap_skips_failures():
    results = [
        make_result("cmd_a", 10, 1.0),
        make_result("cmd_b", 10, 0.0, success=False),
    ]
    commands, sizes, grid = build_heatmap(results)
    assert commands == ["cmd_a"]


def test_build_heatmap_intensity_range():
    results = [
        make_result("cmd_a", 10, 0.0),
        make_result("cmd_a", 20, 1.0),
    ]
    _, _, grid = build_heatmap(results)
    intensities = [cell.intensity for cell in grid[0]]
    assert intensities[0] == pytest.approx(0.0)
    assert intensities[1] == pytest.approx(1.0)


def test_build_heatmap_missing_cell_is_nan():
    results = [
        make_result("cmd_a", 10, 1.0),
        make_result("cmd_b", 20, 2.0),
    ]
    commands, sizes, grid = build_heatmap(results)
    # cmd_a/size=20 missing, cmd_b/size=10 missing
    assert math.isnan(grid[0][1].mean_time)  # cmd_a, size 20
    assert math.isnan(grid[1][0].mean_time)  # cmd_b, size 10


def test_render_heatmap_table_returns_string():
    results = [
        make_result("fast", 100, 0.1),
        make_result("fast", 200, 0.2),
        make_result("slow", 100, 1.0),
        make_result("slow", 200, 2.0),
    ]
    output = render_heatmap_table(results)
    assert isinstance(output, str)
    assert "fast" in output
    assert "slow" in output
    assert "100" in output


def test_render_heatmap_table_no_data():
    assert render_heatmap_table([]) == "No data."
