"""CLI entry point for variance analysis."""

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.variance import analyze_variance, render_variance_table, VarianceResult


def build_variance_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-variance",
        description="Analyze timing variance and stability per command.",
    )
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("--command", default=None, help="Filter to a single command")
    p.add_argument("--tag", default=None, help="Load only results with this tag")
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return p


def _rows_to_json(rows: List[VarianceResult]) -> str:
    data = [
        {
            "command": r.command,
            "sample_count": r.sample_count,
            "mean_time": r.mean_time,
            "stdev_time": r.stdev_time,
            "cv_percent": r.cv_percent,
            "stability": r.stability,
            "min_time": r.min_time,
            "max_time": r.max_time,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_variance(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = analyze_variance(results, command_filter=args.command)

    if args.format == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_variance_table(rows) + "\n")

    unstable = [r for r in rows if r.stability == "unstable"]
    return 1 if unstable else 0


def main():
    parser = build_variance_parser()
    args = parser.parse_args()
    sys.exit(run_variance(args))


if __name__ == "__main__":
    main()
