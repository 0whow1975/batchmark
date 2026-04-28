"""CLI entry-point for cadence analysis."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.cadence import analyze_cadence, render_cadence_table, CadenceResult
from batchmark.history import load_results


def build_cadence_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Analyse growth-rate cadence per command.")
    parser = sub.add_parser("cadence", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("history_file", help="Path to batchmark history JSON file")
    parser.add_argument("--command", default=None, help="Filter to a single command")
    parser.add_argument("--tag", default=None, help="Load only results with this tag")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    return parser


def _rows_to_json(rows: List[CadenceResult]) -> str:
    data = [
        {
            "command": r.command,
            "ratios": r.ratios,
            "mean_ratio": r.mean_ratio,
            "cv": r.cv,
            "label": r.label,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_cadence(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = analyze_cadence(results, command=args.command)
    if args.format == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_cadence_table(rows) + "\n")
    return 0


def main() -> None:
    parser = build_cadence_parser()
    args = parser.parse_args()
    sys.exit(run_cadence(args))


if __name__ == "__main__":
    main()
