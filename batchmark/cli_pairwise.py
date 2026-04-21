"""CLI entry point for pairwise command comparison."""
import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.pairwise import compare_pair, render_pairwise_table


def build_pairwise_parser(subparsers=None):
    desc = "Compare two commands head-to-head across shared input sizes."
    if subparsers is not None:
        p = subparsers.add_parser("pairwise", help=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-pairwise", description=desc)
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("command_a", help="First command label")
    p.add_argument("command_b", help="Second command label")
    p.add_argument("--tag", default=None, help="Filter results by tag")
    p.add_argument(
        "--tie-threshold",
        type=float,
        default=0.02,
        metavar="FRAC",
        help="Ratio distance from 1.0 considered a tie (default: 0.02)",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return p


def run_pairwise(args, out=None):
    if out is None:
        out = sys.stdout
    results = load_results(args.history_file, tag=args.tag)
    rows = compare_pair(
        results,
        args.command_a,
        args.command_b,
        tie_threshold=args.tie_threshold,
    )
    if args.format == "json":
        data = [
            {
                "size": r.size,
                "command_a": r.command_a,
                "command_b": r.command_b,
                "mean_a": r.mean_a,
                "mean_b": r.mean_b,
                "delta": r.delta,
                "ratio": r.ratio,
                "winner": r.winner,
            }
            for r in rows
        ]
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(render_pairwise_table(rows) + "\n")


def main():
    parser = build_pairwise_parser()
    args = parser.parse_args()
    run_pairwise(args)


if __name__ == "__main__":
    main()
