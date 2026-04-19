"""Sparkline rendering for benchmark timing trends."""
from typing import List
from batchmark.runner import BenchmarkResult

SPARK_CHARS = " ▁▂▃▄▅▆▇█"


def _normalize(values: List[float]) -> List[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def make_sparkline(values: List[float]) -> str:
    """Return a sparkline string for a list of float values."""
    if not values:
        return ""
    if len(values) == 1:
        return SPARK_CHARS[4]
    normed = _normalize(values)
    return "".join(SPARK_CHARS[int(v * (len(SPARK_CHARS) - 1))] for v in normed)


def sparklines_for_results(results: List[BenchmarkResult]) -> dict:
    """Return a dict mapping command -> sparkline string from successful results."""
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for r in results:
        if r.success:
            groups[r.command].append((r.size, r.mean))
    out = {}
    for cmd, pairs in groups.items():
        pairs.sort(key=lambda x: x[0])
        out[cmd] = make_sparkline([v for _, v in pairs])
    return out


def render_sparkline_table(results: List[BenchmarkResult]) -> str:
    """Render a table of commands with their sparklines."""
    lines = sparklines_for_results(results)
    if not lines:
        return "No data."
    col = max(len(cmd) for cmd in lines)
    header = f"{'Command':<{col}}  Trend"
    sep = "-" * len(header)
    rows = [header, sep]
    for cmd, spark in sorted(lines.items()):
        rows.append(f"{cmd:<{col}}  {spark}")
    return "\n".join(rows)
