"""Compute speedup ratios between a baseline command and others."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean


@dataclass
class SpeedupRow:
    command: str
    size: int
    baseline_mean: float
    target_mean: float
    speedup: float          # baseline_mean / target_mean  (>1 means target is faster)
    faster: bool


def compute_speedup(
    results: List[BenchmarkResult],
    baseline_command: str,
) -> List[SpeedupRow]:
    """Return speedup of every non-baseline command relative to *baseline_command*.

    Only sizes present for both the baseline and the target command are included.
    Failed runs are skipped.
    """
    # Build {size: mean_time} for baseline
    baseline: dict = {}
    for r in results:
        if r.command == baseline_command and r.success and r.times:
            baseline[r.size] = mean(r.times)

    rows: List[SpeedupRow] = []
    for r in results:
        if r.command == baseline_command:
            continue
        if not r.success or not r.times:
            continue
        if r.size not in baseline:
            continue
        b_mean = baseline[r.size]
        t_mean = mean(r.times)
        if t_mean == 0:
            continue
        ratio = b_mean / t_mean
        rows.append(
            SpeedupRow(
                command=r.command,
                size=r.size,
                baseline_mean=b_mean,
                target_mean=t_mean,
                speedup=ratio,
                faster=ratio > 1.0,
            )
        )

    rows.sort(key=lambda x: (x.command, x.size))
    return rows


def render_speedup_table(rows: List[SpeedupRow], baseline_command: str) -> str:
    """Render speedup rows as a plain-text table."""
    if not rows:
        return "No speedup data available."

    header = f"Speedup vs baseline: {baseline_command}\n"
    sep = "-" * 68
    col = f"{'Command':<24} {'Size':>8} {'Baseline(s)':>12} {'Target(s)':>10} {'Speedup':>8} {'Faster':>7}"
    lines = [header, sep, col, sep]
    for row in rows:
        tag = "yes" if row.faster else "no"
        lines.append(
            f"{row.command:<24} {row.size:>8} {row.baseline_mean:>12.4f} "
            f"{row.target_mean:>10.4f} {row.speedup:>8.3f}x {tag:>7}"
        )
    lines.append(sep)
    return "\n".join(lines)
