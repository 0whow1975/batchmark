from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class PercentileStats:
    command: str
    size: int
    p50: float
    p90: float
    p95: float
    p99: float
    sample_count: int


def _percentile(sorted_data: List[float], p: float) -> float:
    if not sorted_data:
        raise ValueError("Empty data")
    idx = (len(sorted_data) - 1) * p / 100.0
    lo = int(idx)
    hi = lo + 1
    if hi >= len(sorted_data):
        return sorted_data[lo]
    frac = idx - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


def compute_percentiles(results: List[BenchmarkResult]) -> List[PercentileStats]:
    groups: dict = {}
    for r in results:
        if not r.success:
            continue
        key = (r.command, r.size)
        groups.setdefault(key, []).append(r.elapsed)
    stats = []
    for (cmd, size), times in groups.items():
        s = sorted(times)
        stats.append(PercentileStats(
            command=cmd,
            size=size,
            p50=_percentile(s, 50),
            p90=_percentile(s, 90),
            p95=_percentile(s, 95),
            p99=_percentile(s, 99),
            sample_count=len(s),
        ))
    stats.sort(key=lambda x: (x.command, x.size))
    return stats


def render_percentile_table(stats: List[PercentileStats]) -> str:
    if not stats:
        return "No data."
    header = f"{'Command':<30} {'Size':>8} {'N':>4} {'p50':>8} {'p90':>8} {'p95':>8} {'p99':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in stats:
        rows.append(
            f"{s.command:<30} {s.size:>8} {s.sample_count:>4} "
            f"{s.p50:>8.4f} {s.p90:>8.4f} {s.p95:>8.4f} {s.p99:>8.4f}"
        )
    return "\n".join(rows)
