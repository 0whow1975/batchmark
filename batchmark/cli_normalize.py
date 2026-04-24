"""CLI entry point for the normalize subcommand.

Compares benchmark results relative to a chosen baseline command,
expressing every other command's mean time as a ratio.
"""

import argparse
import json
import sys

from batchmark.history import load_results
from batchmark.normalize import normalize_results, render_normalize_table


def build_normalize_parser(subparsers=None):
    """Build (or register) the argument parser for the 'normalize' subcommand.

    If *subparsers* is provided the parser is attached to it; otherwise a
    standalone :class:`argparse.ArgumentParser` is returned.
    """
    description = (
        "Normalize benchmark results against a baseline command. "
        "Each command's mean time is expressed as a ratio relative to the "
        "baseline (1.0 = same speed, >1.0 = slower, <1.0 = faster)."
    )

    if subparsers is not None:
        parser = subparsers.add_parser(
            "normalize",
            help="Normalize results against a baseline command.",
            description=description,
        )
    else:
        parser = argparse.ArgumentParser(
            prog="batchmark-normalize",
            description=description,
        )

    parser.add_argument(
        "history_file",
        help="Path to the history JSON file produced by 'batchmark run'.",
    )
    parser.add_argument(
        "--baseline",
        required=True,
        metavar="COMMAND",
        help="Command to use as the normalization baseline (ratio = 1.0).",
    )
    parser.add_argument(
        "--tag",
        default=None,
        metavar="TAG",
        help="Filter history to a specific run tag before normalizing.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format (default: table).",
    )

    return parser


def run_normalize(args, out=None):
    """Execute the normalize command using parsed *args*.

    Parameters
    ----------
    args:
        Namespace returned by :func:`build_normalize_parser` ``parse_args``.
    out:
        File-like object to write output to (defaults to *sys.stdout*).
    """
    if out is None:
        out = sys.stdout

    results = load_results(args.history_file, tag=args.tag)

    if not results:
        print("No results found.", file=out)
        return

    rows = normalize_results(results, baseline_command=args.baseline)

    if not rows:
        print(
            f"No rows produced — check that baseline command '{args.baseline}' "
            "exists in the loaded results.",
            file=out,
        )
        return

    if args.fmt == "json":
        data = [
            {
                "command": r.command,
                "size": r.size,
                "baseline_command": r.baseline_command,
                "mean": r.mean,
                "baseline_mean": r.baseline_mean,
                "ratio": r.ratio,
            }
            for r in rows
        ]
        print(json.dumps(data, indent=2), file=out)
    else:
        print(render_normalize_table(rows), file=out)


def main():
    """Standalone entry point for ``batchmark-normalize``."""
    parser = build_normalize_parser()
    args = parser.parse_args()
    run_normalize(args)


if __name__ == "__main__":
    main()
