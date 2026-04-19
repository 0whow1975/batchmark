from __future__ import annotations
import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.percentile import compute_percentiles, render_percentile_table


def build_percentile_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-percentile",
        description="Show percentile stats (p50/p90/p95/p99) from saved results.",
    )
    p.add_argument("history_file", help="Path to history JSON file")
    p.add_argument("--tag", default=None, help="Filter by tag")
    p.add_argument("--format", choices=["table", "json"], default="table")
    return p


def run_percentile(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file, tag=args.tag)
    stats = compute_percentiles(results)
    if args.format == "json":
        data = [
            {
                "command": s.command,
                "size": s.size,
                "p50": s.p50,
                "p90": s.p90,
                "p95": s.p95,
                "p99": s.p99,
                "sample_count": s.sample_count,
            }
            for s in stats
        ]
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(render_percentile_table(stats) + "\n")


def main() -> None:
    parser = build_percentile_parser()
    args = parser.parse_args()
    run_percentile(args)


if __name__ == "__main__":
    main()
