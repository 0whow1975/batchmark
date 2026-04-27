"""CLI entry-point for the momentum analysis sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.momentum import MomentumResult, compute_momentum, render_momentum_table


def build_momentum_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "momentum",
        help="Analyse how consistently command runtimes change across input sizes.",
    )
    p.add_argument("history_file", help="Path to batchmark history JSON file.")
    p.add_argument("--tag", default=None, help="Filter results by tag.")
    p.add_argument("--command", default=None, help="Restrict analysis to one command.")
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format (default: table).",
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=None,
        metavar="SCORE",
        help="Only show rows where |momentum_score| >= SCORE.",
    )
    return p


def _rows_to_json(rows: List[MomentumResult]) -> str:
    data = [
        {
            "command": r.command,
            "sizes": r.sizes,
            "times": r.times,
            "deltas": r.deltas,
            "positive_steps": r.positive_steps,
            "negative_steps": r.negative_steps,
            "momentum_score": r.momentum_score,
            "trend": r.trend,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_momentum(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_momentum(results, command=args.command)

    if args.min_score is not None:
        rows = [r for r in rows if abs(r.momentum_score) >= args.min_score]

    if args.fmt == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_momentum_table(rows) + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="batchmark-momentum")
    sub = parser.add_subparsers(dest="cmd")
    build_momentum_parser(sub)
    args = parser.parse_args()
    if args.cmd is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(run_momentum(args))


if __name__ == "__main__":  # pragma: no cover
    main()
