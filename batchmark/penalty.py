"""Penalty scoring: assign a weighted score to each result based on
mean time, stdev, and failure rate, then rank commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from batchmark.runner import BenchmarkResult


@dataclass
class PenaltyRow:
    command: str
    mean: float
    stdev: float
    failure_rate: float   # 0.0 – 1.0
    score: float          # lower is better
    rank: int


def compute_penalty(
    results: List[BenchmarkResult],
    w_mean: float = 1.0,
    w_stdev: float = 0.5,
    w_failure: float = 2.0,
) -> List[PenaltyRow]:
    """Aggregate results per command and compute a penalty score.

    score = w_mean * mean_time + w_stdev * stdev + w_failure * failure_rate
    """
    from collections import defaultdict

    buckets: dict = defaultdict(list)
    for r in results:
        buckets[r.command].append(r)

    rows: List[PenaltyRow] = []
    for cmd, items in buckets.items():
        times = [r.mean for r in items if r.success]
        failures = [r for r in items if not r.success]
        total = len(items)
        failure_rate = len(failures) / total if total else 0.0

        if not times:
            mean_t = 0.0
            sd = 0.0
        else:
            mean_t = sum(times) / len(times)
            variance = sum((t - mean_t) ** 2 for t in times) / len(times)
            sd = variance ** 0.5

        score = w_mean * mean_t + w_stdev * sd + w_failure * failure_rate
        rows.append(
            PenaltyRow(
                command=cmd,
                mean=mean_t,
                stdev=sd,
                failure_rate=failure_rate,
                score=score,
                rank=0,
            )
        )

    rows.sort(key=lambda r: r.score)
    for i, row in enumerate(rows, 1):
        row.rank = i
    return rows


def render_penalty_table(rows: List[PenaltyRow]) -> str:
    if not rows:
        return "No penalty data."
    header = f"{'Rank':>4}  {'Command':<30}  {'Mean':>8}  {'Stdev':>8}  {'FailRate':>8}  {'Score':>10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"{r.rank:>4}  {r.command:<30}  {r.mean:>8.4f}  {r.stdev:>8.4f}"
            f"  {r.failure_rate:>8.2%}  {r.score:>10.4f}"
        )
    return "\n".join(lines)
