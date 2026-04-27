"""CLI entry-point for the step-down detector."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.stepdown import StepdownPoint, detect_stepdowns, render_stepdown_table


def build_stepdown_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-stepdown",
        description="Detect sudden performance improvements across input sizes.",
    )
    p.add_argument("history_file", help="Path to batchmark history JSON file.")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.20,
        metavar="FRAC",
        help="Minimum fractional time drop to flag (default: 0.20).",
    )
    p.add_argument(
        "--command",
        default=None,
        metavar="CMD",
        help="Restrict analysis to a single command.",
    )
    p.add_argument(
        "--tag",
        default=None,
        metavar="TAG",
        help="Load only results with this tag from the history file.",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format (default: table).",
    )
    return p


def _points_to_json(points: List[StepdownPoint]) -> str:
    data = [
        {
            "command": p.command,
            "size_before": p.size_before,
            "size_after": p.size_after,
            "time_before": p.time_before,
            "time_after": p.time_after,
            "drop_ratio": p.drop_ratio,
            "drop_pct": p.drop_pct,
        }
        for p in points
    ]
    return json.dumps(data, indent=2)


def run_stepdown(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file, tag=args.tag)
    points = detect_stepdowns(results, threshold=args.threshold, command=args.command)
    if args.fmt == "json":
        out.write(_points_to_json(points) + "\n")
    else:
        out.write(render_stepdown_table(points) + "\n")


def main() -> None:  # pragma: no cover
    parser = build_stepdown_parser()
    args = parser.parse_args()
    run_stepdown(args)


if __name__ == "__main__":  # pragma: no cover
    main()
