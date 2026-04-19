import json
from typing import List
from batchmark.runner import BenchmarkResult


def result_to_dict(result: BenchmarkResult) -> dict:
    return {
        "command": result.command,
        "input_size": result.input_size,
        "runs": result.runs,
        "mean_s": round(result.mean, 6),
        "median_s": round(result.median, 6),
        "stdev_s": round(result.stdev, 6),
        "min_s": round(result.min, 6),
        "max_s": round(result.max, 6),
        "success_rate": round(result.success_rate, 4),
        "error": result.error,
    }


def render_json(results: List[BenchmarkResult]) -> str:
    return json.dumps([result_to_dict(r) for r in results], indent=2)


def render_table(results: List[BenchmarkResult]) -> str:
    headers = ["command", "input_size", "mean_s", "median_s", "stdev_s", "min_s", "max_s", "ok%"]
    rows = []
    for r in results:
        rows.append([
            r.command,
            str(r.input_size),
            f"{r.mean:.4f}",
            f"{r.median:.4f}",
            f"{r.stdev:.4f}",
            f"{r.min:.4f}",
            f"{r.max:.4f}",
            f"{r.success_rate * 100:.1f}%",
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def fmt_row(cells):
        return "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(cells))

    separator = "  ".join("-" * w for w in col_widths)
    lines = [fmt_row(headers), separator] + [fmt_row(r) for r in rows]
    return "\n".join(lines)
