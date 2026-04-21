"""CLI entry point for baseline set/compare commands."""

import argparse
import sys
from batchmark.history import load_results
from batchmark.baseline import set_baseline, load_baseline, diff_against_baseline, render_baseline_table


def build_baseline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-baseline",
        description="Manage and compare against saved baselines.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_set = sub.add_parser("set", help="Save results from history as baseline")
    p_set.add_argument("history_file", help="Path to history JSON file")
    p_set.add_argument("--tag", default="baseline", help="Tag to read from history")
    p_set.add_argument("--baseline-file", default="baseline.json", help="Output baseline file")
    p_set.add_argument("--baseline-tag", default="baseline", help="Tag to store baseline under")

    p_cmp = sub.add_parser("compare", help="Compare current history results against baseline")
    p_cmp.add_argument("history_file", help="Path to current history JSON file")
    p_cmp.add_argument("--history-tag", default=None, help="Tag to read current results from")
    p_cmp.add_argument("--baseline-file", default="baseline.json", help="Baseline JSON file")
    p_cmp.add_argument("--baseline-tag", default="baseline", help="Tag for baseline entries")
    p_cmp.add_argument("--threshold", type=float, default=0.10, help="Regression threshold (default 0.10)")
    p_cmp.add_argument("--fail-on-regression", action="store_true", help="Exit with code 1 if any regression found")

    return parser


def run_baseline(args: argparse.Namespace) -> int:
    if args.subcommand == "set":
        results = load_results(args.history_file, tag=args.tag)
        if not results:
            print("No results found for given tag.", file=sys.stderr)
            return 1
        set_baseline(results, args.baseline_file, tag=args.baseline_tag)
        print(f"Baseline saved to {args.baseline_file} (tag={args.baseline_tag}), {len(results)} result(s).")
        return 0

    if args.subcommand == "compare":
        current = load_results(args.history_file, tag=args.history_tag)
        if not current:
            print("No current results found for the given history file/tag.", file=sys.stderr)
            return 1
        baseline = load_baseline(args.baseline_file, tag=args.baseline_tag)
        if not baseline:
            print("Baseline is empty or not found.", file=sys.stderr)
            return 1
        diffs = diff_against_baseline(baseline, current, regression_threshold=args.threshold)
        print(render_baseline_table(diffs))
        if args.fail_on_regression and any(d.regression for d in diffs):
            print("\nRegressions detected.", file=sys.stderr)
            return 1
        return 0

    return 0


def main():
    parser = build_baseline_parser()
    args = parser.parse_args()
    sys.exit(run_baseline(args))


if __name__ == "__main__":
    main()
