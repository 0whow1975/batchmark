"""CLI entry point for throttle detection."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import List

from batchmark.history import load_results
from batchmark.throttle import detect_throttle, render_throttle_table


def build_throttle_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    desc = "Detect commands with super-linear runtime growth."
    if sub is not None:
        p = sub.add_parser("throttle", help=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-throttle", description=desc)
    p.add_argument("history_file", help="Path to history JSON file.")
    p.add_argument("--tag", default=None, help="Filter by tag.")
    p.add_argument(
        "--threshold",
        type=float,
        default=1.2,
        help="Super-linear detection threshold (default: 1.2).",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    return p


def run_throttle(args: argparse.Namespace) -> None:
    results = load_results(args.history_file, tag=args.tag)
    rows = detect_throttle(results, threshold=args.threshold)

    if args.format == "json":
        print(json.dumps([asdict(r) for r in rows], indent=2))
    else:
        print(render_throttle_table(rows))

    flagged = [r for r in rows if r.superlinear]
    if flagged:
        sys.exit(1)


def main() -> None:
    parser = build_throttle_parser()
    args = parser.parse_args()
    run_throttle(args)


if __name__ == "__main__":
    main()
