"""Export benchmark results to CSV and Markdown formats."""

import csv
import io
from typing import List

from batchmark.report import result_to_dict
from batchmark.runner import BenchmarkResult


def render_csv(results: List[BenchmarkResult]) -> str:
    """Render benchmark results as a CSV string."""
    if not results:
        return ""

    fieldnames = ["label", "size", "runs", "mean", "median", "stdev", "min", "max", "success"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for result in results:
        writer.writerow(result_to_dict(result))
    return output.getvalue()


def render_markdown(results: List[BenchmarkResult]) -> str:
    """Render benchmark results as a Markdown table."""
    if not results:
        return ""

    headers = ["Label", "Size", "Runs", "Mean (s)", "Median (s)", "Stdev (s)", "Min (s)", "Max (s)", "OK"]
    sep = ["---"] * len(headers)

    rows = []
    for result in results:
        d = result_to_dict(result)
        rows.append([
            str(d.get("label", "")),
            str(d.get("size", "")),
            str(d.get("runs", "")),
            f"{d.get('mean', 0):.4f}",
            f"{d.get('median', 0):.4f}",
            f"{d.get('stdev', 0):.4f}",
            f"{d.get('min', 0):.4f}",
            f"{d.get('max', 0):.4f}",
            "yes" if d.get("success") else "no",
        ])

    def fmt_row(cols):
        return "| " + " | ".join(cols) + " |"

    lines = [fmt_row(headers), fmt_row(sep)]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines) + "\n"
