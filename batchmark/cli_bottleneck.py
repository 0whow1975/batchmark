"""CLI entry-point for the bottleneck sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.bottleneck import BottleneckEntry, find_bottlenecks, render_bottleneck_table
from batchmark.history import load_results


def build_bottleneck_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Identify commands/sizes that dominate total benchmark time."
    if sub is not None:
        p = sub.add_parser("bottleneck", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-bottleneck", description=desc)
    p.add_argument("history_file", help="Path to history JSON file.")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        metavar="FRAC",
        help="Minimum share of total time to flag as bottleneck (default: 0.10).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N entries.",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format (default: table).",
    )
    return p


def _entry_to_dict(e: BottleneckEntry) -> dict:
    return {
        "command": e.command,
        "size": e.size,
        "mean_time": round(e.mean_time, 6),
        "total_share": round(e.total_share, 6),
        "is_bottleneck": e.is_bottleneck,
    }


def run_bottleneck(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file)
    entries = find_bottlenecks(results, threshold=args.threshold)
    if args.top is not None:
        entries = entries[: args.top]

    if args.fmt == "json":
        out.write(json.dumps([_entry_to_dict(e) for e in entries], indent=2))
        out.write("\n")
    else:
        out.write(render_bottleneck_table(entries))
        out.write("\n")


def main(argv=None) -> None:
    parser = build_bottleneck_parser()
    args = parser.parse_args(argv)
    run_bottleneck(args)


if __name__ == "__main__":
    main()
