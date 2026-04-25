"""CLI entry-point for the convergence detection sub-command."""
from __future__ import annotations
import argparse
import json
import sys
from typing import List

from batchmark.convergence import detect_convergence, render_convergence_table, ConvergenceResult
from batchmark.history import load_results


def build_convergence_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Detect commands whose runtime converges as input size grows."
    if sub is not None:
        p = sub.add_parser("convergence", help=desc)
    else:
        p = argparse.ArgumentParser(prog="batchmark-convergence", description=desc)
    p.add_argument("history_file", help="Path to history JSON file.")
    p.add_argument("--window", type=int, default=3, help="Window size for mean comparison (default: 3).")
    p.add_argument("--threshold", type=float, default=5.0, help="Delta %% threshold to consider converged (default: 5.0).")
    p.add_argument("--command", default=None, help="Filter to a specific command.")
    p.add_argument("--format", choices=["table", "json"], default="table", dest="fmt")
    return p


def _rows_to_json(rows: List[ConvergenceResult]) -> str:
    out = []
    for r in rows:
        out.append({
            "command": r.command,
            "sizes": r.sizes,
            "means": r.means,
            "delta_pct": r.delta_pct,
            "converged": r.converged,
            "window": r.window,
        })
    return json.dumps(out, indent=2)


def run_convergence(args: argparse.Namespace, out=sys.stdout) -> None:
    results = load_results(args.history_file)
    if args.command:
        results = [r for r in results if r.command == args.command]
    rows = detect_convergence(results, window=args.window, threshold_pct=args.threshold)
    if args.fmt == "json":
        out.write(_rows_to_json(rows) + "\n")
    else:
        out.write(render_convergence_table(rows) + "\n")


def main() -> None:  # pragma: no cover
    parser = build_convergence_parser()
    args = parser.parse_args()
    run_convergence(args)


if __name__ == "__main__":  # pragma: no cover
    main()
