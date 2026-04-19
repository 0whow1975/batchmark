import json
from unittest.mock import patch, MagicMock
from batchmark.runner import BenchmarkResult
from batchmark.cli_filter import build_filter_parser, run_filter


def make_result(command="cmd", input_size=100, times=None, success=True):
    return BenchmarkResult(
        command=command,
        input_size=input_size,
        times=times or [0.1, 0.2],
        success=success,
        exit_code=0,
        timed_out=False,
    )


def test_build_filter_parser_defaults():
    parser = build_filter_parser()
    args = parser.parse_args(["history.json"])
    assert args.history_file == "history.json"
    assert args.command is None
    assert args.success_only is False
    assert args.fmt == "table"
    assert args.top is None


def test_run_filter_table(capsys):
    results = [make_result("echo", 100), make_result("cat", 200)]
    args = build_filter_parser().parse_args(["h.json"])
    with patch("batchmark.cli_filter.load_results", return_value=results):
        run_filter(args)
    out = capsys.readouterr().out
    assert "echo" in out or "cat" in out


def test_run_filter_json(capsys):
    results = [make_result("echo", 100)]
    args = build_filter_parser().parse_args(["h.json", "--format", "json"])
    with patch("batchmark.cli_filter.load_results", return_value=results):
        run_filter(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["command"] == "echo"


def test_run_filter_command(capsys):
    results = [make_result("echo"), make_result("cat")]
    args = build_filter_parser().parse_args(["h.json", "--command", "echo"])
    with patch("batchmark.cli_filter.load_results", return_value=results):
        run_filter(args)
    out = capsys.readouterr().out
    assert "echo" in out


def test_run_filter_no_results(capsys):
    args = build_filter_parser().parse_args(["h.json"])
    with patch("batchmark.cli_filter.load_results", return_value=[]):
        run_filter(args)
    err = capsys.readouterr().err
    assert "No results" in err


def test_run_filter_top(capsys):
    results = [
        make_result("slow", times=[1.0, 1.0]),
        make_result("fast", times=[0.01, 0.01]),
        make_result("mid", times=[0.5, 0.5]),
    ]
    args = build_filter_parser().parse_args(["h.json", "--top", "1"])
    with patch("batchmark.cli_filter.load_results", return_value=results):
        run_filter(args)
    out = capsys.readouterr().out
    assert "fast" in out
