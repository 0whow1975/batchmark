"""Headroom analysis: how much room each command has before hitting a time budget."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult, mean


@dataclass
class HeadroomResult:
    command: str
    size: int
    mean_time: float
    budget: float
    headroom: float          # budget - mean_time  (negative => over budget)
    headroom_pct: float      # headroom / budget * 100
    within_budget: bool


def compute_headroom(
    results: List[BenchmarkResult],
    budget: float,
    command: Optional[str] = None,
) -> List[HeadroomResult]:
    """Return headroom rows for each (command, size) pair.

    Args:
        results: benchmark results to analyse.
        budget:  time budget in seconds.
        command: if given, restrict analysis to this command.
    """
    rows: List[HeadroomResult] = []
    for r in results:
        if not r.success:
            continue
        if command and r.command != command:
            continue
        if not r.times:
            continue
        m = mean(r.times)
        hw = budget - m
        pct = (hw / budget * 100.0) if budget > 0 else 0.0
        rows.append(
            HeadroomResult(
                command=r.command,
                size=r.size,
                mean_time=m,
                budget=budget,
                headroom=hw,
                headroom_pct=pct,
                within_budget=hw >= 0,
            )
        )
    rows.sort(key=lambda x: (x.command, x.size))
    return rows


def render_headroom_table(rows: List[HeadroomResult]) -> str:
    """Render headroom results as a plain-text table."""
    if not rows:
        return "No headroom data."
    header = f"{'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Budget(s)':>10} {'Headroom(s)':>12} {'Headroom%':>10} {'OK':>4}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        ok = "yes" if r.within_budget else "NO"
        lines.append(
            f"{r.command:<30} {r.size:>8} {r.mean_time:>10.4f} {r.budget:>10.4f}"
            f" {r.headroom:>+12.4f} {r.headroom_pct:>9.1f}% {ok:>4}"
        )
    return "\n".join(lines)
