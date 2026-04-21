"""Identify commands and sizes that dominate total benchmark time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from batchmark.runner import BenchmarkResult


@dataclass
class BottleneckEntry:
    command: str
    size: int
    mean_time: float
    total_share: float   # fraction of grand-total mean time (0-1)
    is_bottleneck: bool  # True when share >= threshold


def find_bottlenecks(
    results: List[BenchmarkResult],
    threshold: float = 0.1,
) -> List[BottleneckEntry]:
    """Return one entry per (command, size) pair sorted by share descending.

    *threshold* is the minimum fraction of total time for a pair to be
    flagged as a bottleneck (default 10 %).
    """
    if not results:
        return []

    successes = [r for r in results if r.success and r.times]
    if not successes:
        return []

    pair_means: dict[tuple[str, int], float] = {}
    for r in successes:
        mean_t = sum(r.times) / len(r.times)
        pair_means[(r.command, r.size)] = mean_t

    grand_total = sum(pair_means.values())
    if grand_total == 0:
        return []

    entries = [
        BottleneckEntry(
            command=cmd,
            size=sz,
            mean_time=mt,
            total_share=mt / grand_total,
            is_bottleneck=(mt / grand_total) >= threshold,
        )
        for (cmd, sz), mt in pair_means.items()
    ]
    entries.sort(key=lambda e: e.total_share, reverse=True)
    return entries


def render_bottleneck_table(entries: List[BottleneckEntry]) -> str:
    """Render a plain-text table of bottleneck entries."""
    if not entries:
        return "No data."

    header = f"{'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Share%':>8} {'Flag'}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        flag = "<< BOTTLENECK" if e.is_bottleneck else ""
        rows.append(
            f"{e.command:<30} {e.size:>8} {e.mean_time:>10.4f} "
            f"{e.total_share * 100:>7.1f}% {flag}"
        )
    return "\n".join(rows)
