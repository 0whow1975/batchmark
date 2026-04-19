"""CLI entry point for sparkline trend visualization."""
import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.sparkline import render_sparkline_table, sparklines_for_results


def build_sparkline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-sparkline",
        description="Render sparkline trends from benchmark history.",
    )
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("--tag", default=None, help="Filter by tag")
    p.add_argument(
        "--format", choices=["table", "json"], default="table",
        dest="fmt", help="Output format"
    )
    return p


def run_sparkline(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file, tag=args.tag)
    if not results:
        out.write("No results found.\n")
        return
    if args.fmt == "json":
        data = sparklines_for_results(results)
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(render_sparkline_table(results) + "\n")


def main() -> None:
    parser = build_sparkline_parser()
    args = parser.parse_args()
    run_sparkline(args)


if __name__ == "__main__":
    main()
