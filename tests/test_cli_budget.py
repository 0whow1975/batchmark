"""Tests for batchmark.cli_budget."""

import json
import pytest
from unittest.mock import patch, MagicMock
from batchmark.cli_budget import build_budget_parser, run_budget
from batchmark.runner import BenchmarkResult


def make_result(command="grep", size=100, mean=1.0, failed=False):
    return BenchmarkResult(
        command=command,
        size=size,
        times=[] if failed else [mean],
        mean=mean,
        median=mean,
        stdev=0.0,
        min=mean,
        max=mean,
        failed=failed,
    )


def test_build_budget_parser_defaults():
    parser = build_budget_parser()
    args = parser.parse_args(["history.json", "--budget", "1.0"])
    assert args.history_file == "history.json"
    assert args.budget == 1.0
    assert args.command is None
    assert args.tag is None
    assert args.format == "table"
    assert not args.fail_on_over


def test_build_budget_parser_all_flags():
    parser = build_budget_parser()
    args = parser.parse_args([
        "history.json", "--budget", "0.5",
        "--command", "grep", "--tag", "v1",
        "--format", "json", "--fail-on-over",
    ])
    assert args.budget == 0.5
    assert args.command == "grep"
    assert args.tag == "v1"
    assert args.format == "json"
    assert args.fail_on_over


def test_run_budget_table_output(capsys):
    results = [make_result(mean=0.5), make_result(size=200, mean=1.5)]
    parser = build_budget_parser()
    args = parser.parse_args(["history.json", "--budget", "1.0"])
    with patch("batchmark.cli_budget.load_results", return_value=results):
        code = run_budget(args)
    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert "OVER" in captured.out
    assert code == 0


def test_run_budget_json_output(capsys):
    results = [make_result(mean=0.5)]
    parser = build_budget_parser()
    args = parser.parse_args(["history.json", "--budget", "1.0", "--format", "json"])
    with patch("batchmark.cli_budget.load_results", return_value=results):
        code = run_budget(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["exceeded"] is False
    assert code == 0


def test_run_budget_fail_on_over():
    results = [make_result(mean=2.0)]
    parser = build_budget_parser()
    args = parser.parse_args(["history.json", "--budget", "1.0", "--fail-on-over"])
    with patch("batchmark.cli_budget.load_results", return_value=results):
        code = run_budget(args)
    assert code == 1


def test_run_budget_no_fail_when_under():
    results = [make_result(mean=0.3)]
    parser = build_budget_parser()
    args = parser.parse_args(["history.json", "--budget", "1.0", "--fail-on-over"])
    with patch("batchmark.cli_budget.load_results", return_value=results):
        code = run_budget(args)
    assert code == 0
