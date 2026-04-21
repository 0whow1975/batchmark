"""CLI entry-point for the rerank sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.rerank import VALID_METRICS, RerankRow, rerank_results, render_rerank_table


def build_rerank_parser(subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(description="Re-rank benchmark results by a chosen metric.")
    if subparsers is not None:
        parser = subparsers.add_parser("rerank", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("history_file", help="Path to history JSON file.")
    parser.add_argument(
        "--metric",
        choices=VALID_METRICS,
        default="mean",
        help="Metric to rank by (default: mean).",
    )
    parser.add_argument(
        "--desc",
        action="store_true",
        help="Sort descending (slowest first).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only top N results.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="fmt",
        help="Output format (default: table).",
    )
    return parser


def _rows_to_json(rows: List[RerankRow]) -> str:
    data = [
        {
            "rank": r.rank,
            "command": r.command,
            "size": r.size,
            "metric": r.metric,
            "value": r.value,
            "runs": r.runs,
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_rerank(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file)
    rows = rerank_results(
        results,
        metric=args.metric,
        ascending=not args.desc,
        top_n=args.top,
    )
    if args.fmt == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_rerank_table(rows) + "\n")


def main() -> None:  # pragma: no cover
    parser = build_rerank_parser()
    args = parser.parse_args()
    run_rerank(args)


if __name__ == "__main__":  # pragma: no cover
    main()
