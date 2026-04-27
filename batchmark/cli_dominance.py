"""CLI entry point for dominance analysis."""

import argparse
import json
import sys
from typing import List

from batchmark.dominance import compute_dominance, render_dominance_table, DominanceRow
from batchmark.history import load_results


def build_dominance_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-dominance",
        description="Find commands that dominate others across all input sizes.",
    )
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("--tag", default=None, help="Filter results by tag")
    p.add_argument(
        "--command",
        action="append",
        dest="commands",
        metavar="CMD",
        help="Restrict analysis to these commands (repeatable)",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    p.add_argument(
        "--strict-only",
        action="store_true",
        default=False,
        help="Only show strictly dominant relationships",
    )
    return p


def _rows_to_json(rows: List[DominanceRow]) -> str:
    data = [
        {
            "winner": r.winner,
            "loser": r.loser,
            "sizes_compared": r.sizes_compared,
            "min_speedup": r.min_speedup,
            "max_speedup": r.max_speedup,
            "avg_speedup": r.avg_speedup,
            "strict": r.strict,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_dominance(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_dominance(results, command_filter=args.commands)

    if args.strict_only:
        rows = [r for r in rows if r.strict]

    if args.format == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_dominance_table(rows) + "\n")
    return 0


def main() -> None:
    parser = build_dominance_parser()
    args = parser.parse_args()
    sys.exit(run_dominance(args))


if __name__ == "__main__":
    main()
