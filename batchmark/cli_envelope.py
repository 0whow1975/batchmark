"""CLI entry point for the envelope subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from batchmark.history import load_results
from batchmark.envelope import build_envelope, render_envelope_table
from batchmark.runner import BenchmarkResult


def build_envelope_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "envelope",
        help="Show min/max time envelope per (command, size) across stored results.",
    )
    p.add_argument("--history", required=True, help="Path to history JSON file.")
    p.add_argument("--tag", default=None, help="Filter history by tag.")
    p.add_argument("--command", default=None, help="Restrict to a single command.")
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    return p


def _envelope_to_dict(e) -> dict:  # type: ignore[type-arg]
    return {
        "command": e.command,
        "size": e.size,
        "lo": round(e.lo, 6),
        "hi": round(e.hi, 6),
        "spread": round(e.spread, 6),
        "spread_pct": round(e.spread_pct, 2),
    }


def run_envelope(args: argparse.Namespace, out=sys.stdout) -> None:
    results: List[BenchmarkResult] = load_results(args.history, tag=args.tag)
    envelope = build_envelope(results, command_filter=args.command)

    if args.format == "json":
        data = [_envelope_to_dict(e) for e in sorted(envelope.values(), key=lambda x: (x.command, x.size))]
        out.write(json.dumps(data, indent=2))
        out.write("\n")
    else:
        out.write(render_envelope_table(envelope))
        out.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="batchmark-envelope")
    sub = parser.add_subparsers(dest="cmd")
    build_envelope_parser(sub)
    args = parser.parse_args()
    if args.cmd is None:
        parser.print_help()
        sys.exit(1)
    run_envelope(args)
