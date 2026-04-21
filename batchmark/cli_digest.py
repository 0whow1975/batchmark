"""CLI entry point for the digest subcommand."""

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.digest import build_digest, render_digest_table, DigestEntry


def build_digest_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Show a concise digest of benchmark results grouped by command."
    if subparsers is not None:
        parser = subparsers.add_parser("digest", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="batchmark-digest", description=desc)

    parser.add_argument("history_file", help="Path to the history JSON file.")
    parser.add_argument(
        "--tag", default=None, help="Filter results by tag before digesting."
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    return parser


def _entry_to_dict(e: DigestEntry) -> dict:
    return {
        "command": e.command,
        "sample_count": e.sample_count,
        "mean_time": round(e.mean_time, 6),
        "median_time": round(e.median_time, 6),
        "stdev_time": round(e.stdev_time, 6),
        "min_time": round(e.min_time, 6),
        "failure_count": e.failure_count,
        "success_rate": round(e.success_rate, 4),
    }


def run_digest(args: argparse.Namespace, out=sys.stdout) -> int:
    results = load_results(args.history_file, tag=args.tag)
    if not results:
        print("No results found.", file=out)
        return 0

    entries = build_digest(results)

    if args.format == "json":
        print(json.dumps([_entry_to_dict(e) for e in entries], indent=2), file=out)
    else:
        print(render_digest_table(entries), file=out)

    return 0


def main():
    parser = build_digest_parser()
    args = parser.parse_args()
    sys.exit(run_digest(args))


if __name__ == "__main__":
    main()
