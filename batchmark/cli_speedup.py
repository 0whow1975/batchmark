"""CLI entry point for the speedup sub-command."""

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.speedup import SpeedupRow, compute_speedup, render_speedup_table


def build_speedup_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Show speedup ratios of commands relative to a baseline command."
    if sub is not None:
        p = sub.add_parser("speedup", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-speedup", description=desc)
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("baseline", help="Name of the baseline command")
    p.add_argument("--tag", default=None, help="Filter history by tag")
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return p


def _rows_to_json(rows: List[SpeedupRow]) -> str:
    data = [
        {
            "command": r.command,
            "size": r.size,
            "baseline_mean": round(r.baseline_mean, 6),
            "target_mean": round(r.target_mean, 6),
            "speedup": round(r.speedup, 6),
            "faster": r.faster,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_speedup(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_speedup(results, baseline_command=args.baseline)

    if args.format == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_speedup_table(rows, baseline_command=args.baseline) + "\n")
    return 0


def main():  # pragma: no cover
    parser = build_speedup_parser()
    args = parser.parse_args()
    sys.exit(run_speedup(args))


if __name__ == "__main__":  # pragma: no cover
    main()
