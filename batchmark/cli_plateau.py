"""CLI entry point for plateau detection."""

import argparse
import json
from batchmark.history import load_results
from batchmark.plateau import detect_plateaus, render_plateau_table


def build_plateau_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark-plateau",
        description="Detect plateau regions in benchmark results.",
    )
    parser.add_argument("history_file", help="Path to history JSON file")
    parser.add_argument("--tag", default=None, help="Filter by tag")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Max variance %% to qualify as plateau (default: 10.0)",
    )
    parser.add_argument(
        "--min-points",
        type=int,
        default=3,
        help="Minimum consecutive sizes to form a plateau (default: 3)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser


def run_plateau(args: argparse.Namespace) -> None:
    results = load_results(args.history_file, tag=args.tag)
    regions = detect_plateaus(
        results,
        threshold_pct=args.threshold,
        min_points=args.min_points,
    )

    if args.format == "json":
        data = [
            {
                "command": r.command,
                "start_size": r.start_size,
                "end_size": r.end_size,
                "avg_time": r.avg_time,
                "variance_pct": r.variance_pct,
                "is_plateau": r.is_plateau,
            }
            for r in regions
        ]
        print(json.dumps(data, indent=2))
    else:
        print(render_plateau_table(regions))


def main() -> None:
    parser = build_plateau_parser()
    args = parser.parse_args()
    run_plateau(args)


if __name__ == "__main__":
    main()
