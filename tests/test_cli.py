import json
import pytest
from unittest.mock import patch, MagicMock
from batchmark.cli import build_parser, main
from batchmark.runner import BenchmarkResult


def make_result(size, error=None):
    return BenchmarkResult(
        command=f"echo {size}",
        size=size,
        runs=[0.1, 0.2, 0.15],
        error=error,
    )


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["echo {size}", "--sizes", "10", "100"])
    assert args.command == "echo {size}"
    assert args.sizes == [10, 100]
    assert args.runs == 5
    assert args.timeout == 30.0
    assert args.output_format == "table"


def test_build_parser_all_flags():
    parser = build_parser()
    args = parser.parse_args(
        ["cmd", "--sizes", "1", "2", "--runs", "3", "--timeout", "10", "--format", "json"]
    )
    assert args.runs == 3
    assert args.timeout == 10.0
    assert args.output_format == "json"


@patch("batchmark.cli.run_benchmark")
def test_main_table_output(mock_run, capsys):
    mock_run.side_effect = [make_result(10), make_result(100)]
    ret = main(["echo {size}", "--sizes", "10", "100", "--runs", "3"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "10" in out
    assert "100" in out


@patch("batchmark.cli.run_benchmark")
def test_main_json_output(mock_run, capsys):
    mock_run.side_effect = [make_result(50)]
    ret = main(["echo {size}", "--sizes", "50", "--format", "json"])
    assert ret == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["size"] == 50


@patch("batchmark.cli.run_benchmark")
def test_main_returns_1_on_error(mock_run):
    mock_run.return_value = make_result(10, error="timeout")
    ret = main(["bad_cmd", "--sizes", "10"])
    assert ret == 1
