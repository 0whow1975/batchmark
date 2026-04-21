"""CLI entry point for scaling analysis.

Analyzes how command runtime scales with input size by fitting
linear, quadratic, and logarithmic models and reporting the best fit.
"""

import argparse
import json
import sys

from batchmark.history import load_results
from batchmark.scaling import analyze_scaling, render_scaling_table


def build_scaling_parser(subparsers=None):
    """Build the argument parser for the scaling subcommand."""
    description = "Analyze how command runtime scales with input size."

    if subparsers is not None:
        parser = subparsers.add_parser("scaling", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="batchmark-scaling", description=description)

    parser.add_argument(
        "history_file",
        help="Path to the history JSON file produced by batchmark.",
    )
    parser.add_argument(
        "--tag",
        default=None,
        metavar="TAG",
        help="Filter results to a specific history tag.",
    )
    parser.add_argument(
        "--command",
        default=None,
        metavar="CMD",
        help="Restrict analysis to a single command substring match.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--min-points",
        type=int,
        default=3,
        metavar="N",
        help="Minimum number of distinct sizes required to fit a model (default: 3).",
    )
    return parser


def _result_to_dict(sr):
    """Serialize a ScalingResult to a plain dict for JSON output."""
    return {
        "command": sr.command,
        "best_fit": sr.best_fit,
        "r2": round(sr.r2, 6),
        "models": {
            model: {"r2": round(metrics["r2"], 6), "coeffs": metrics["coeffs"]}
            for model, metrics in sr.models.items()
        },
    }


def run_scaling(args, out=None):
    """Execute scaling analysis and write output.

    Parameters
    ----------
    args:
        Parsed namespace from :func:`build_scaling_parser`.
    out:
        File-like object to write output to (defaults to stdout).
    """
    if out is None:
        out = sys.stdout

    results = load_results(args.history_file, tag=args.tag)

    if args.command:
        results = [r for r in results if args.command in r.command]

    scaling_results = analyze_scaling(results, min_points=args.min_points)

    if args.fmt == "json":
        payload = [_result_to_dict(sr) for sr in scaling_results]
        out.write(json.dumps(payload, indent=2))
        out.write("\n")
    else:
        table = render_scaling_table(scaling_results)
        out.write(table)
        out.write("\n")


def main():
    """Standalone entry point for batchmark-scaling."""
    parser = build_scaling_parser()
    args = parser.parse_args()
    run_scaling(args)


if __name__ == "__main__":
    main()
