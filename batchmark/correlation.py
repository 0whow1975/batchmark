"""Correlation analysis between input size and execution time.

Computes Pearson and Spearman correlation coefficients for each command,
helping identify how strongly timing scales with input size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict, Sequence

from batchmark.runner import BenchmarkResult


@dataclass
class CorrelationResult:
    """Correlation statistics for a single command."""
    command: str
    n: int                   # number of data points
    pearson: float           # Pearson r  (-1 to 1)
    spearman: float          # Spearman rho (-1 to 1)
    interpretation: str      # human-readable strength label


def _pearson(xs: List[float], ys: List[float]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(xs)
    if n < 2:
        return float("nan")
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def _rank(values: List[float]) -> List[float]:
    """Return rank of each value (1-based, average ranks for ties)."""
    sorted_vals = sorted(enumerate(values), key=lambda t: t[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(sorted_vals):
        j = i
        # find run of equal values
        while j + 1 < len(sorted_vals) and sorted_vals[j + 1][1] == sorted_vals[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1  # 1-based average
        for k in range(i, j + 1):
            ranks[sorted_vals[k][0]] = avg_rank
        i = j + 1
    return ranks


def _spearman(xs: List[float], ys: List[float]) -> float:
    """Compute Spearman rank correlation coefficient."""
    if len(xs) < 2:
        return float("nan")
    return _pearson(_rank(xs), _rank(ys))


def _interpret(r: float) -> str:
    """Map a correlation coefficient to a human-readable label."""
    if math.isnan(r):
        return "n/a"
    a = abs(r)
    if a >= 0.9:
        return "very strong"
    if a >= 0.7:
        return "strong"
    if a >= 0.5:
        return "moderate"
    if a >= 0.3:
        return "weak"
    return "negligible"


def compute_correlations(
    results: Sequence[BenchmarkResult],
) -> List[CorrelationResult]:
    """Compute per-command Pearson and Spearman correlations.

    Only successful results are included.  Commands with fewer than 2
    successful data points are skipped.
    """
    # group by command
    groups: Dict[str, List[BenchmarkResult]] = {}
    for r in results:
        if not r.success:
            continue
        groups.setdefault(r.command, []).append(r)

    output: List[CorrelationResult] = []
    for cmd, rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        xs = [float(r.size) for r in rows]
        ys = [r.mean_time for r in rows]
        p = _pearson(xs, ys)
        s = _spearman(xs, ys)
        output.append(
            CorrelationResult(
                command=cmd,
                n=len(rows),
                pearson=p,
                spearman=s,
                interpretation=_interpret(p),
            )
        )
    return output


def render_correlation_table(rows: List[CorrelationResult]) -> str:
    """Render correlation results as a plain-text table."""
    if not rows:
        return "No correlation data available."

    header = f"{'Command':<30} {'N':>4}  {'Pearson r':>10}  {'Spearman ρ':>10}  {'Strength'}"
    sep = "-" * len(header)
    lines = [header, sep]
    for row in rows:
        p_str = f"{row.pearson:+.4f}" if not math.isnan(row.pearson) else "   n/a"
        s_str = f"{row.spearman:+.4f}" if not math.isnan(row.spearman) else "   n/a"
        lines.append(
            f"{row.command:<30} {row.n:>4}  {p_str:>10}  {s_str:>10}  {row.interpretation}"
        )
    return "\n".join(lines)
