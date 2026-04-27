"""CLI entry-point for headroom analysis."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.headroom import HeadroomResult, compute_headroom, render_headroom_table
from batchmark.history import load_results


def build_headroom_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Show how much time budget headroom each command has.")
    parser = sub.add_parser("headroom", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("history_file", help="Path to history JSON file.")
    parser.add_argument("--budget", type=float, required=True, help="Time budget in seconds.")
    parser.add_argument("--command", default=None, help="Filter to a single command.")
    parser.add_argument("--tag", default=None, help="Load only results with this tag.")
    parser.add_argument("--format", choices=["table", "json"], default="table", dest="fmt")
    parser.add_argument("--fail-on-over", action="store_true", help="Exit 1 if any result exceeds budget.")
    return parser


def _rows_to_json(rows: List[HeadroomResult]) -> str:
    data = [
        {
            "command": r.command,
            "size": r.size,
            "mean_time": r.mean_time,
            "budget": r.budget,
            "headroom": r.headroom,
            "headroom_pct": r.headroom_pct,
            "within_budget": r.within_budget,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_headroom(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_headroom(results, budget=args.budget, command=args.command)

    if args.fmt == "json":
        print(_rows_to_json(rows), file=out)
    else:
        print(render_headroom_table(rows), file=out)

    if args.fail_on_over and any(not r.within_budget for r in rows):
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_headroom_parser()
    args = parser.parse_args()
    sys.exit(run_headroom(args))


if __name__ == "__main__":  # pragma: no cover
    main()
