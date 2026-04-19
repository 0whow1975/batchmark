"""CLI subcommand: batchmark compare — compare two commands side by side."""

import argparse
import sys
from batchmark.runner import run_benchmark
from batchmark.compare import compare_results, render_comparison_table


def build_compare_parser(subparsers=None):
    description = "Compare two or more commands across input sizes."
    if subparsers is not None:
        parser = subparsers.add_parser("compare", description=description)
    else:
        parser = argparse.ArgumentParser(prog="batchmark compare", description=description)

    parser.add_argument("commands", nargs="+", help="Commands to compare (quote each)")
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=[100, 1000, 10000],
        metavar="N", help="Input sizes to benchmark (default: 100 1000 10000)"
    )
    parser.add_argument(
        "--runs", type=int, default=3,
        help="Number of timed runs per size (default: 3)"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0,
        help="Timeout in seconds per run (default: 30)"
    )
    parser.add_argument(
        "--labels", nargs="+", metavar="LABEL",
        help="Optional labels for each command (must match count)"
    )
    return parser


def run_compare(args) -> int:
    commands = args.commands
    labels = args.labels if args.labels else commands

    if len(labels) != len(commands):
        print(
            f"Error: --labels count ({len(labels)}) must match commands count ({len(commands)}).",
            file=sys.stderr,
        )
        return 1

    groups = {}
    for label, cmd in zip(labels, commands):
        results = []
        for size in args.sizes:
            result = run_benchmark(
                command=cmd,
                input_size=size,
                runs=args.runs,
                timeout=args.timeout,
            )
            results.append(result)
        groups[label] = results

    comparison = compare_results(groups)
    print(render_comparison_table(comparison))
    return 0


def main():
    parser = build_compare_parser()
    args = parser.parse_args()
    sys.exit(run_compare(args))


if __name__ == "__main__":
    main()
