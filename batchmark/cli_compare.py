"""CLI entry point for the compare subcommand.

Allows users to compare benchmark results from two saved history tags
and render a side-by-side comparison table or JSON output.
"""

import argparse
import json
import sys

from batchmark.history import load_results
from batchmark.compare import compare_results, render_comparison_table


def build_compare_parser(subparsers=None):
    """Build the argument parser for the compare subcommand.

    Args:
        subparsers: Optional subparsers action to attach this parser to.

    Returns:
        The constructed ArgumentParser (or subcommand parser).
    """
    description = "Compare benchmark results between two history tags."

    if subparsers is not None:
        parser = subparsers.add_parser("compare", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="batchmark-compare", description=description)

    parser.add_argument(
        "baseline_tag",
        help="History tag to use as the baseline (reference) run.",
    )
    parser.add_argument(
        "candidate_tag",
        help="History tag to use as the candidate (new) run.",
    )
    parser.add_argument(
        "--history-file",
        default="batchmark_history.jsonl",
        help="Path to the history JSONL file (default: batchmark_history.jsonl).",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: 'table' (default) or 'json'.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Relative change threshold to flag regressions (default: 0.05 = 5%%).",
    )
    return parser


def run_compare(args, out=None):
    """Execute the compare command using parsed arguments.

    Args:
        args: Parsed argparse namespace.
        out: Output stream (defaults to sys.stdout).
    """
    if out is None:
        out = sys.stdout

    baseline_results = load_results(args.history_file, tag=args.baseline_tag)
    candidate_results = load_results(args.history_file, tag=args.candidate_tag)

    if not baseline_results:
        print(
            f"[error] No results found for baseline tag '{args.baseline_tag}' "
            f"in '{args.history_file}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not candidate_results:
        print(
            f"[error] No results found for candidate tag '{args.candidate_tag}' "
            f"in '{args.history_file}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    rows = compare_results(baseline_results, candidate_results, threshold=args.threshold)

    if args.format == "json":
        output = [
            {
                "command": r.command,
                "size": r.size,
                "baseline_mean": r.baseline_mean,
                "candidate_mean": r.candidate_mean,
                "delta": r.delta,
                "relative_change": r.relative_change,
                "regression": r.regression,
            }
            for r in rows
        ]
        print(json.dumps(output, indent=2), file=out)
    else:
        print(render_comparison_table(rows), file=out)


def main():
    """Entry point for the batchmark-compare CLI tool."""
    parser = build_compare_parser()
    args = parser.parse_args()
    run_compare(args)


if __name__ == "__main__":
    main()
