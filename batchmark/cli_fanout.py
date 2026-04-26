"""cli_fanout.py — CLI entry point for the fanout analysis sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.fanout import FanoutResult, compute_fanout, render_fanout_table
from batchmark.history import load_results


def build_fanout_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Detect commands with high runtime spread across input sizes.")
    parser = sub.add_parser("fanout", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("history_file", help="Path to batchmark history JSON file.")
    parser.add_argument(
        "--threshold", type=float, default=3.0,
        help="Spread ratio >= threshold marks a command as fanned-out (default: 3.0).",
    )
    parser.add_argument("--command", default=None, help="Restrict analysis to a single command.")
    parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        dest="fmt", help="Output format (default: table).",
    )
    parser.add_argument("--tag", default=None, help="Filter history by tag.")
    return parser


def _rows_to_json(rows: List[FanoutResult]) -> str:
    data = [
        {
            "command": r.command,
            "min_time": r.min_time,
            "max_time": r.max_time,
            "spread": r.spread,
            "spread_ratio": r.spread_ratio if r.spread_ratio != float("inf") else None,
            "sizes_measured": r.sizes_measured,
            "flagged": r.flagged,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_fanout(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_fanout(results, threshold=args.threshold, command_filter=args.command)

    if args.fmt == "json":
        print(_rows_to_json(rows), file=out)
    else:
        print(render_fanout_table(rows), file=out)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_fanout_parser()
    args = parser.parse_args()
    sys.exit(run_fanout(args))


if __name__ == "__main__":  # pragma: no cover
    main()
