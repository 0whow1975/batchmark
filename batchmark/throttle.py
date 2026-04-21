"""Throttle detection: identify commands whose runtime grows faster than linear."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class ThrottleResult:
    command: str
    size: int
    elapsed: float
    ratio: Optional[float]          # elapsed / prev_elapsed; None for first point
    superlinear: bool               # True when ratio > size_ratio * threshold


def detect_throttle(
    results: List[BenchmarkResult],
    threshold: float = 1.2,
) -> List[ThrottleResult]:
    """Detect super-linear growth per command.

    For each command, results are sorted by size.  Consecutive pairs are
    compared: if (time_ratio / size_ratio) > threshold the point is flagged
    as super-linear (throttled).

    Args:
        results:   Flat list of BenchmarkResult objects.
        threshold: Multiplier above the expected linear ratio to flag.

    Returns:
        List of ThrottleResult, one per (command, size) data point.
    """
    from collections import defaultdict

    by_cmd: dict = defaultdict(list)
    for r in results:
        if r.success:
            by_cmd[r.command].append(r)

    output: List[ThrottleResult] = []
    for cmd, pts in by_cmd.items():
        pts_sorted = sorted(pts, key=lambda r: r.size)
        prev: Optional[BenchmarkResult] = None
        for cur in pts_sorted:
            if prev is None:
                output.append(ThrottleResult(cmd, cur.size, cur.elapsed, None, False))
            else:
                size_ratio = cur.size / prev.size if prev.size else 1.0
                time_ratio = cur.elapsed / prev.elapsed if prev.elapsed else 1.0
                superlinear = (time_ratio / size_ratio) > threshold
                output.append(
                    ThrottleResult(cmd, cur.size, cur.elapsed, time_ratio, superlinear)
                )
            prev = cur
    return output


def render_throttle_table(rows: List[ThrottleResult]) -> str:
    """Render throttle results as a plain-text table."""
    if not rows:
        return "No throttle data."

    header = f"{'Command':<30} {'Size':>10} {'Elapsed':>10} {'TimeRatio':>10} {'Flag':>6}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        ratio_str = f"{r.ratio:.3f}" if r.ratio is not None else "     -"
        flag = "SLOW" if r.superlinear else "ok"
        lines.append(
            f"{r.command:<30} {r.size:>10} {r.elapsed:>10.4f} {ratio_str:>10} {flag:>6}"
        )
    return "\n".join(lines)
