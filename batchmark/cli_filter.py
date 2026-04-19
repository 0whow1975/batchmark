"""CLI sub-tool: filter and display results from history."""

import argparse
import sys
from batchmark.history import load_results
from batchmark.filter import filter_results, top_n
from batchmark.report import render_table, render_json


def build_filter_parser(parent=None):
    kwargs = dict(description="Filter benchmark results from history.")
    parser = argparse.ArgumentParser(**kwargs) if parent is None else parent
    parser.add_argument("history_file", help="Path to history JSON file")
    parser.add_argument("--command", default=None, help="Filter by exact command")
    parser.add_argument("--min-size", type=int, default=None)
    parser.add_argument("--max-size", type=int, default=None)
    parser.add_argument("--success-only", action="store_true")
    parser.add_argument(
        "--top", type=int, default=None, metavar="N",
        help="Show top N results by mean time"
    )
    parser.add_argument(
        "--sort-key", default="mean", choices=["mean", "median", "min", "max"]
    )
    parser.add_argument(
        "--format", dest="fmt", default="table", choices=["table", "json"]
    )
    parser.add_argument("--tag", default=None, help="Filter history by tag")
    return parser


def run_filter(args):
    results = load_results(args.history_file, tag=args.tag)
    if not results:
        print("No results found.", file=sys.stderr)
        return

    filtered = filter_results(
        results,
        command=args.command,
        min_size=args.min_size,
        max_size=args.max_size,
        success_only=args.success_only,
    )

    if args.top is not None:
        filtered = top_n(filtered, n=args.top, key=args.sort_key)

    if not filtered:
        print("No results match the given filters.", file=sys.stderr)
        return

    if args.fmt == "json":
        print(render_json(filtered))
    else:
        print(render_table(filtered))


def main():
    parser = build_filter_parser()
    args = parser.parse_args()
    run_filter(args)


if __name__ == "__main__":
    main()
