"""CLI entry-point for the slowdown detection sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.slowdown import detect_slowdowns, render_slowdown_table


def build_slowdown_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Detect commands that slow down disproportionately at larger input sizes."
    if sub is not None:
        p = sub.add_parser("slowdown", help=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-slowdown", description=desc)

    p.add_argument("history_file", help="Path to history JSON file produced by batchmark.")
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Ratio above which a result is flagged (default: 2.0).",
    )
    p.add_argument(
        "--tag",
        default=None,
        help="Filter history to a specific tag.",
    )
    p.add_argument(
        "--flagged-only",
        action="store_true",
        help="Only show flagged (slow) entries.",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    return p


def run_slowdown(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file, tag=args.tag)
    rows = detect_slowdowns(results, threshold=args.threshold)

    if args.flagged_only:
        rows = [r for r in rows if r.flagged]

    if args.format == "json":
        data = [
            {
                "command": r.command,
                "size": r.size,
                "mean_time": r.mean_time,
                "ratio": r.ratio,
                "flagged": r.flagged,
                "baseline_size": r.baseline_size,
                "baseline_mean": r.baseline_mean,
            }
            for r in rows
        ]
        out.write(json.dumps(data, indent=2))
        out.write("\n")
    else:
        out.write(render_slowdown_table(rows))
        out.write("\n")


def main() -> None:  # pragma: no cover
    parser = build_slowdown_parser()
    args = parser.parse_args()
    run_slowdown(args)


if __name__ == "__main__":  # pragma: no cover
    main()
