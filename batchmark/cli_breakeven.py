"""CLI entry point for breakeven analysis."""
import argparse
import json
import sys
from batchmark.history import load_results
from batchmark.breakeven import find_breakeven, render_breakeven_table


def build_breakeven_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Find the input size where one command overtakes another in performance."
    if sub is not None:
        p = sub.add_parser("breakeven", help=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-breakeven", description=desc)
    p.add_argument("--history", required=True, metavar="FILE",
                   help="Path to history JSON file")
    p.add_argument("--tag", default=None, metavar="TAG",
                   help="Filter history by tag")
    p.add_argument("--a", dest="command_a", required=True,
                   help="First command (baseline)")
    p.add_argument("--b", dest="command_b", required=True,
                   help="Second command (challenger)")
    p.add_argument("--format", choices=["table", "json"], default="table",
                   dest="fmt", help="Output format (default: table)")
    return p


def run_breakeven(args, out=None):
    if out is None:
        out = sys.stdout
    results = load_results(args.history, tag=args.tag)
    result = find_breakeven(results, args.command_a, args.command_b)
    if args.fmt == "json":
        ta = dict(zip(result.sizes_a, result.times_a))
        tb = dict(zip(result.sizes_b, result.times_b))
        payload = {
            "command_a": result.command_a,
            "command_b": result.command_b,
            "breakeven_size": result.breakeven_size,
            "a_wins_below": result.a_wins_below,
            "series": [
                {
                    "size": s,
                    "time_a": ta.get(s),
                    "time_b": tb.get(s),
                }
                for s in sorted(set(result.sizes_a) | set(result.sizes_b))
            ],
        }
        out.write(json.dumps(payload, indent=2))
        out.write("\n")
    else:
        out.write(render_breakeven_table(result))
        out.write("\n")


def main():
    parser = build_breakeven_parser()
    args = parser.parse_args()
    run_breakeven(args)


if __name__ == "__main__":
    main()
