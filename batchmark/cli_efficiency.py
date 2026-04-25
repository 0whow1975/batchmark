"""CLI entry point for the efficiency sub-command."""
import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.efficiency import compute_efficiency, render_efficiency_table, EfficiencyRow


def build_efficiency_parser(subparsers=None):
    description = "Compute efficiency scores (size / mean_time) for benchmarked commands."
    if subparsers is not None:
        parser = subparsers.add_parser("efficiency", help=description)
    else:
        parser = argparse.ArgumentParser(prog="batchmark-efficiency", description=description)

    parser.add_argument("history_file", help="Path to history JSON file.")
    parser.add_argument("--command", default=None, help="Filter to a specific command.")
    parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        dest="output_format", help="Output format (default: table)."
    )
    parser.add_argument("--tag", default=None, help="Filter results by tag.")
    return parser


def _rows_to_json(rows: List[EfficiencyRow]) -> str:
    data = [
        {
            "rank": r.rank,
            "command": r.command,
            "size": r.size,
            "mean_time": r.mean_time,
            "efficiency": r.efficiency,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_efficiency(args, out=None):
    if out is None:
        out = sys.stdout

    results = load_results(args.history_file, tag=args.tag)
    rows = compute_efficiency(results, command=args.command)

    if args.output_format == "json":
        print(_rows_to_json(rows), file=out)
    else:
        print(render_efficiency_table(rows), file=out)


def main():
    parser = build_efficiency_parser()
    args = parser.parse_args()
    run_efficiency(args)


if __name__ == "__main__":
    main()
