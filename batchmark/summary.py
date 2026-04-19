"""Aggregate summary statistics across a collection of BenchmarkResults."""

from typing import List, Dict, Any
from batchmark.runner import BenchmarkResult, mean, median, stdev, min as bmin


def summarize(
    results: List[BenchmarkResult],
    group_by: str = "command",
) -> List[Dict[str, Any]]:
    """Return summary rows grouped by 'command' or 'input_size'."""
    if group_by not in ("command", "input_size"):
        raise ValueError("group_by must be 'command' or 'input_size'")

    groups: Dict[Any, List[BenchmarkResult]] = {}
    for r in results:
        key = r.command if group_by == "command" else r.input_size
        groups.setdefault(key, []).append(r)

    rows = []
    for key, group in sorted(groups.items(), key=lambda x: str(x[0])):
        all_times = [t for r in group if r.success for t in r.times]
        total_runs = len(group)
        successful = sum(1 for r in group if r.success)
        row: Dict[str, Any] = {
            group_by: key,
            "total_runs": total_runs,
            "successful": successful,
            "failed": total_runs - successful,
        }
        if all_times:
            row["mean"] = round(mean(all_times), 6)
            row["median"] = round(median(all_times), 6)
            row["stdev"] = round(stdev(all_times), 6) if len(all_times) > 1 else 0.0
            row["min"] = round(bmin(all_times), 6)
            row["max"] = round(max(all_times), 6)
        else:
            row.update({"mean": None, "median": None, "stdev": None, "min": None, "max": None})
        rows.append(row)
    return rows


def render_summary_table(rows: List[Dict[str, Any]], group_by: str = "command") -> str:
    """Render summary rows as a plain-text table."""
    headers = [group_by, "runs", "ok", "fail", "mean", "median", "min", "max"]
    lines = ["  ".join(f"{h:>10}" for h in headers)]
    lines.append("-" * (12 * len(headers)))
    for row in rows:
        def fmt(v):
            if v is None:
                return "N/A"
            if isinstance(v, float):
                return f"{v:.4f}"
            return str(v)
        cells = [
            fmt(row[group_by]),
            fmt(row["total_runs"]),
            fmt(row["successful"]),
            fmt(row["failed"]),
            fmt(row["mean"]),
            fmt(row["median"]),
            fmt(row["min"]),
            fmt(row["max"]),
        ]
        lines.append("  ".join(f"{c:>10}" for c in cells))
    return "\n".join(lines)
