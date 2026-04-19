import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.regression import detect_regressions, render_regression_table


def build_regression_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-regression",
        description="Detect performance regressions between two result sets.",
    )
    p.add_argument("baseline_file", help="Path to baseline results JSON")
    p.add_argument("current_file", help="Path to current results JSON")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Regression threshold as fraction (default: 0.10)",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    p.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with code 1 if any regressions are detected",
    )
    return p


def run_regression(args: argparse.Namespace) -> None:
    baseline = load_results(args.baseline_file)
    current = load_results(args.current_file)
    rows = detect_regressions(baseline, current, threshold=args.threshold)

    if args.format == "json":
        data = [
            {
                "command": r.command,
                "size": r.size,
                "baseline_mean": r.baseline_mean,
                "current_mean": r.current_mean,
                "delta": r.delta,
                "pct_change": r.pct_change,
                "is_regression": r.is_regression,
            }
            for r in rows
        ]
        print(json.dumps(data, indent=2))
    else:
        print(render_regression_table(rows))

    if args.fail_on_regression and any(r.is_regression for r in rows):
        sys.exit(1)


def main():
    parser = build_regression_parser()
    args = parser.parse_args()
    run_regression(args)


if __name__ == "__main__":
    main()
