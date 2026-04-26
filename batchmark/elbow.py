"""Elbow point detection: find the input size where marginal cost increases sharply."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class ElbowResult:
    command: str
    elbow_size: Optional[int]          # input size at elbow, or None
    elbow_mean: Optional[float]        # mean time at elbow size
    max_curvature_index: Optional[int] # index in sorted size list
    sizes: List[int]
    means: List[float]


def _curvature(xs: List[float], ys: List[float]) -> List[float]:
    """Return a discrete curvature proxy for each interior point."""
    scores = [0.0] * len(xs)
    for i in range(1, len(xs) - 1):
        # second-difference approximation normalised by x-spacing
        dx1 = xs[i] - xs[i - 1]
        dx2 = xs[i + 1] - xs[i]
        if dx1 == 0 or dx2 == 0:
            continue
        d1 = (ys[i] - ys[i - 1]) / dx1
        d2 = (ys[i + 1] - ys[i]) / dx2
        scores[i] = abs(d2 - d1)
    return scores


def detect_elbows(results: List[BenchmarkResult]) -> List[ElbowResult]:
    """Detect elbow points per command across input sizes."""
    from batchmark.filter import group_by_command

    groups = group_by_command(results)
    output: List[ElbowResult] = []

    for cmd, items in sorted(groups.items()):
        valid = [r for r in items if r.success and r.times]
        if len(valid) < 3:
            output.append(ElbowResult(cmd, None, None, None, [], []))
            continue

        valid.sort(key=lambda r: r.size)
        sizes = [r.size for r in valid]
        means = [sum(r.times) / len(r.times) for r in valid]

        xs = [float(s) for s in sizes]
        scores = _curvature(xs, means)
        best_i = max(range(len(scores)), key=lambda i: scores[i])

        output.append(ElbowResult(
            command=cmd,
            elbow_size=sizes[best_i],
            elbow_mean=means[best_i],
            max_curvature_index=best_i,
            sizes=sizes,
            means=means,
        ))

    return output


def render_elbow_table(rows: List[ElbowResult]) -> str:
    header = f"{'Command':<30} {'Elbow Size':>12} {'Mean (s)':>12} {'# Sizes':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        if r.elbow_size is None:
            lines.append(f"{r.command:<30} {'n/a':>12} {'n/a':>12} {len(r.sizes):>8}")
        else:
            lines.append(
                f"{r.command:<30} {r.elbow_size:>12} {r.elbow_mean:>12.4f} {len(r.sizes):>8}"
            )
    return "\n".join(lines)
