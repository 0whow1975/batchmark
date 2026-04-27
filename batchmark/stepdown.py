"""Detect step-down (sudden improvement) points in benchmark timing series."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from batchmark.runner import BenchmarkResult


@dataclass
class StepdownPoint:
    command: str
    size_before: int
    size_after: int
    time_before: float
    time_after: float
    drop_ratio: float   # time_after / time_before  (< 1.0 means faster)
    drop_pct: float     # percentage improvement


def detect_stepdowns(
    results: List[BenchmarkResult],
    threshold: float = 0.20,
    command: str | None = None,
) -> List[StepdownPoint]:
    """Return points where mean time drops by at least *threshold* fraction.

    Args:
        results:   flat list of BenchmarkResult objects.
        threshold: minimum fractional drop to flag (default 0.20 = 20%).
        command:   if given, restrict analysis to this command.
    """
    from collections import defaultdict

    grouped: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for r in results:
        if r.failed:
            continue
        if command and r.command != command:
            continue
        grouped[r.command].append(r)

    points: List[StepdownPoint] = []
    for cmd, runs in grouped.items():
        runs.sort(key=lambda r: r.size)
        for i in range(1, len(runs)):
            prev = runs[i - 1]
            curr = runs[i]
            if prev.mean == 0:
                continue
            ratio = curr.mean / prev.mean
            if ratio < 1.0 - threshold:
                points.append(
                    StepdownPoint(
                        command=cmd,
                        size_before=prev.size,
                        size_after=curr.size,
                        time_before=prev.mean,
                        time_after=curr.mean,
                        drop_ratio=ratio,
                        drop_pct=(1.0 - ratio) * 100.0,
                    )
                )
    return points


def render_stepdown_table(points: List[StepdownPoint]) -> str:
    """Render detected step-down points as a plain-text table."""
    if not points:
        return "No step-down points detected."

    header = f"{'Command':<30} {'Size Before':>12} {'Size After':>12} "
    header += f"{'Before (s)':>12} {'After (s)':>12} {'Drop %':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for p in points:
        rows.append(
            f"{p.command:<30} {p.size_before:>12} {p.size_after:>12} "
            f"{p.time_before:>12.4f} {p.time_after:>12.4f} {p.drop_pct:>7.1f}%"
        )
    return "\n".join(rows)
