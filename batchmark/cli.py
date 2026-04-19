import argparse
import sys
from batchmark.runner import run_benchmark
from batchmark.report import render_json, render_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark",
        description="Benchmark shell commands across multiple input sizes.",
    )
    parser.add_argument("command", help="Shell command to benchmark (use {size} as placeholder)")
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        required=True,
        metavar="N",
        help="Input sizes to benchmark against",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        metavar="N",
        help="Number of runs per size (default: 5)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        metavar="SEC",
        help="Timeout in seconds per run (default: 30)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    results = []
    for size in args.sizes:
        cmd = args.command.replace("{size}", str(size))
        result = run_benchmark(cmd, size=size, runs=args.runs, timeout=args.timeout)
        results.append(result)

    if args.output_format == "json":
        print(render_json(results))
    else:
        print(render_table(results))

    failed = [r for r in results if r.error]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
