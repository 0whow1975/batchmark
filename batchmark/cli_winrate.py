"""CLI entry point for win-rate analysis."""
import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.winrate import compute_win_rates, render_winrate_table


def build_winrate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="batchmark-winrate",
        description="Show win rates between every pair of benchmarked commands.",
    )
    p.add_argument("history_file", help="Path to batchmark history JSON file")
    p.add_argument("--tag", default=None, help="Filter results by tag")
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return p


def _rows_to_json(rows) -> str:
    data = [
        {
            "command_a": r.command_a,
            "command_b": r.command_b,
            "wins_a": r.wins_a,
            "wins_b": r.wins_b,
            "ties": r.ties,
            "total": r.total,
            "win_rate_a": round(r.win_rate_a, 4),
            "win_rate_b": round(r.win_rate_b, 4),
        }
        for r in rows
    ]
    return json.dumps(data, indent=2)


def run_winrate(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file, tag=args.tag)
    rows = compute_win_rates(results)
    if args.format == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_winrate_table(rows) + "\n")


def main() -> None:
    parser = build_winrate_parser()
    args = parser.parse_args()
    run_winrate(args)


if __name__ == "__main__":
    main()
