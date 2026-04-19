import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.outlier import detect_outliers, render_outlier_table


def build_outlier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-outlier",
        description="Detect outlier benchmark results from a history file.",
    )
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Z-score threshold to flag outliers (default: 2.0)",
    )
    p.add_argument(
        "--tag",
        default=None,
        help="Filter results by tag",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="fmt",
        help="Output format (default: table)",
    )
    p.add_argument(
        "--only-outliers",
        action="store_true",
        help="Only show flagged outlier rows",
    )
    return p


def run_outlier(args: argparse.Namespace) -> None:
    results = load_results(args.history_file, tag=args.tag)
    if not results:
        print("No results found.", file=sys.stderr)
        return

    annotated = detect_outliers(results, threshold=args.threshold)

    if args.only_outliers:
        annotated = [o for o in annotated if o.is_outlier]

    if args.fmt == "json":
        output = [
            {
                "command": o.result.command,
                "size": o.result.size,
                "z_score": o.z_score,
                "is_outlier": o.is_outlier,
            }
            for o in annotated
        ]
        print(json.dumps(output, indent=2))
    else:
        print(render_outlier_table(annotated))


def main() -> None:
    parser = build_outlier_parser()
    args = parser.parse_args()
    run_outlier(args)


if __name__ == "__main__":
    main()
