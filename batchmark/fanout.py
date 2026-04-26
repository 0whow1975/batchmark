"""fanout.py — detect commands whose runtime spreads (fans out) across sizes.

A command 'fans out' when its spread (max - min) across input sizes grows
disproportionately compared to other commands, indicating high sensitivity
to input size.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class FanoutResult:
    command: str
    min_time: float
    max_time: float
    spread: float          # max_time - min_time
    spread_ratio: float    # max_time / min_time  (inf if min == 0)
    sizes_measured: int
    flagged: bool          # True when spread_ratio >= threshold


def compute_fanout(
    results: List[BenchmarkResult],
    threshold: float = 3.0,
    command_filter: Optional[str] = None,
) -> List[FanoutResult]:
    """Compute fanout metrics per command.

    Args:
        results: flat list of BenchmarkResult objects.
        threshold: spread_ratio >= threshold marks a command as flagged.
        command_filter: if given, restrict to this command only.

    Returns:
        List of FanoutResult sorted by spread_ratio descending.
    """
    from collections import defaultdict

    buckets: dict[str, list[float]] = defaultdict(list)
    for r in results:
        if not r.success:
            continue
        if command_filter and r.command != command_filter:
            continue
        buckets[r.command].append(r.mean_time)

    rows: List[FanoutResult] = []
    for cmd, times in buckets.items():
        if len(times) < 2:
            continue
        lo = min(times)
        hi = max(times)
        spread = hi - lo
        ratio = (hi / lo) if lo > 0 else float("inf")
        rows.append(
            FanoutResult(
                command=cmd,
                min_time=lo,
                max_time=hi,
                spread=spread,
                spread_ratio=ratio,
                sizes_measured=len(times),
                flagged=ratio >= threshold,
            )
        )

    rows.sort(key=lambda r: r.spread_ratio, reverse=True)
    return rows


def render_fanout_table(rows: List[FanoutResult]) -> str:
    """Render fanout results as a plain-text table."""
    if not rows:
        return "No fanout data available."

    header = f"{'Command':<30} {'Min':>9} {'Max':>9} {'Spread':>9} {'Ratio':>7} {'Sizes':>6} {'Flag':>5}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        flag = "YES" if r.flagged else "-"
        ratio_str = f"{r.spread_ratio:.2f}x" if r.spread_ratio != float("inf") else "inf"
        lines.append(
            f"{r.command:<30} {r.min_time:>9.4f} {r.max_time:>9.4f}"
            f" {r.spread:>9.4f} {ratio_str:>7} {r.sizes_measured:>6} {flag:>5}"
        )
    return "\n".join(lines)
