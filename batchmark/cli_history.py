"""CLI sub-tool to inspect batchmark history."""

import argparse
import sys

from batchmark.history import load_results, list_tags, HISTORY_FILE
from batchmark.report import render_table, render_json


def build_history_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-history",
        description="Inspect saved benchmark history.",
    )
    parser.add_argument(
        "--file", default=HISTORY_FILE, help="Path to history file."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("tags", help="List available tags in history.")

    show = sub.add_parser("show", help="Show results from history.")
    show.add_argument("--tag", default=None, help="Filter by tag.")
    show.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format.",
    )
    return parser


def run_history(args: argparse.Namespace) -> None:
    if args.command == "tags":
        tags = list_tags(path=args.file)
        if not tags:
            print("No tags found.")
        else:
            for t in tags:
                print(t)
        return

    if args.command == "show":
        results = load_results(path=args.file, tag=args.tag)
        if not results:
            print("No results found.")
            return
        if args.fmt == "json":
            print(render_json(results))
        else:
            print(render_table(results))


def main() -> None:
    parser = build_history_parser()
    args = parser.parse_args()
    run_history(args)


if __name__ == "__main__":
    main()
