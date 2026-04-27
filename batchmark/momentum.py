"""Momentum analysis: measures how consistently a command improves (or degrades)
across successive input sizes by computing the sign-consistency of time deltas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class MomentumResult:
    command: str
    sizes: List[int]
    times: List[float]
    deltas: List[float]          # time[i+1] - time[i]
    positive_steps: int          # deltas > 0  (slowing down)
    negative_steps: int          # deltas < 0  (speeding up)
    momentum_score: float        # in [-1.0, 1.0]; positive = consistently slower
    trend: str                   # "accelerating", "decelerating", "mixed", "flat"


def _trend_label(score: float) -> str:
    if score > 0.6:
        return "decelerating"
    if score < -0.6:
        return "accelerating"
    if abs(score) <= 0.15:
        return "flat"
    return "mixed"


def compute_momentum(
    results: List[BenchmarkResult],
    command: Optional[str] = None,
) -> List[MomentumResult]:
    """Compute momentum for each command (optionally filtered).

    Results with success=False are skipped.  At least two successful data
    points per command are required to produce a MomentumResult.
    """
    from collections import defaultdict

    buckets: dict = defaultdict(list)
    for r in results:
        if not r.success:
            continue
        if command and r.command != command:
            continue
        buckets[r.command].append(r)

    out: List[MomentumResult] = []
    for cmd, rows in sorted(buckets.items()):
        rows.sort(key=lambda r: r.size)
        if len(rows) < 2:
            continue
        sizes = [r.size for r in rows]
        times = [r.mean for r in rows]
        deltas = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        pos = sum(1 for d in deltas if d > 0)
        neg = sum(1 for d in deltas if d < 0)
        total = len(deltas)
        score = (pos - neg) / total if total else 0.0
        out.append(MomentumResult(
            command=cmd,
            sizes=sizes,
            times=times,
            deltas=deltas,
            positive_steps=pos,
            negative_steps=neg,
            momentum_score=round(score, 4),
            trend=_trend_label(score),
        ))
    return out


def render_momentum_table(rows: List[MomentumResult]) -> str:
    if not rows:
        return "No momentum data available."
    header = f"{'Command':<30} {'Points':>6} {'Score':>7} {'Trend':<14}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"{r.command:<30} {len(r.sizes):>6} {r.momentum_score:>7.3f} {r.trend:<14}"
        )
    return "\n".join(lines)
