"""Detect commands whose runtime slows down disproportionately at large input sizes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult, mean


@dataclass
class SlowdownResult:
    command: str
    size: int
    mean_time: float
    ratio: float          # mean_time / baseline_mean_time
    flagged: bool
    baseline_size: int
    baseline_mean: float


def detect_slowdowns(
    results: List[BenchmarkResult],
    threshold: float = 2.0,
) -> List[SlowdownResult]:
    """Compare each (command, size) pair against the smallest size for that command.

    A result is flagged when ratio >= threshold.
    Skips failed results and commands with fewer than 2 distinct sizes.
    """
    from collections import defaultdict

    # Group successful results by command then by size
    by_cmd: dict = defaultdict(lambda: defaultdict(list))
    for r in results:
        if not r.success:
            continue
        by_cmd[r.command][r.size].append(r)

    output: List[SlowdownResult] = []
    for command, size_map in by_cmd.items():
        sizes = sorted(size_map.keys())
        if len(sizes) < 2:
            continue

        baseline_size = sizes[0]
        baseline_mean = mean([r.elapsed for r in size_map[baseline_size]])
        if baseline_mean == 0:
            continue

        for size in sizes:
            m = mean([r.elapsed for r in size_map[size]])
            ratio = m / baseline_mean
            output.append(
                SlowdownResult(
                    command=command,
                    size=size,
                    mean_time=m,
                    ratio=ratio,
                    flagged=ratio >= threshold,
                    baseline_size=baseline_size,
                    baseline_mean=baseline_mean,
                )
            )

    return output


def render_slowdown_table(rows: List[SlowdownResult]) -> str:
    """Render a plain-text table of slowdown results."""
    if not rows:
        return "No slowdown data."

    header = f"{'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Ratio':>8} {'Flag':>6}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        flag = "YES" if r.flagged else "-"
        lines.append(
            f"{r.command:<30} {r.size:>8} {r.mean_time:>10.4f} {r.ratio:>8.2f} {flag:>6}"
        )
    return "\n".join(lines)
