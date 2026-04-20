"""CLI entry point for budget enforcement checks."""

import argparse
import json
import sys
from typing import List

from batchmark.budget import check_budget, render_budget_table
from batchmark.history import load_results
from batchmark.report import result_to_dict


def build_budget_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-budget",
        description="Check benchmark results against a time budget.",
    )
    parser.add_argument("history_file", help="Path to history JSON file.")
    parser.add_argument(
        "--budget",
        type=float,
        required=True,
        help="Maximum allowed mean time in seconds.",
    )
    parser.add_argument(
        "--command",
        default=None,
        help="Filter to a specific command.",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Load only results with this tag from history.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--fail-on-over",
        action="store_true",
        help="Exit with code 1 if any result exceeds the budget.",
    )
    return parser


def run_budget(args: argparse.Namespace) -> int:
    results = load_results(args.history_file, tag=args.tag)
    budget_results = check_budget(results, budget=args.budget, command=args.command)

    if args.format == "json":
        out = []
        for br in budget_results:
            d = result_to_dict(br.result)
            d["budget"] = br.budget
            d["delta"] = br.delta
            d["exceeded"] = br.exceeded
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        print(render_budget_table(budget_results))

    if args.fail_on_over and any(br.exceeded for br in budget_results):
        return 1
    return 0


def main():
    parser = build_budget_parser()
    args = parser.parse_args()
    sys.exit(run_budget(args))


if __name__ == "__main__":
    main()
