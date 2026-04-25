"""Detect convergence: commands whose runtime stabilizes as input size grows."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class ConvergenceResult:
    command: str
    sizes: List[int]
    means: List[float]
    delta_pct: Optional[float]   # % change from first to last window mean
    converged: bool
    window: int


def detect_convergence(
    results: List[BenchmarkResult],
    window: int = 3,
    threshold_pct: float = 5.0,
) -> List[ConvergenceResult]:
    """Return a ConvergenceResult per command.

    A command is considered converged when the absolute percentage change
    between the mean of the first *window* sizes and the last *window* sizes
    is below *threshold_pct*.
    """
    from collections import defaultdict

    grouped: dict = defaultdict(list)
    for r in results:
        if r.success:
            grouped[r.command].append(r)

    output: List[ConvergenceResult] = []
    for cmd, runs in grouped.items():
        runs.sort(key=lambda r: r.size)
        sizes = [r.size for r in runs]
        means = [r.mean for r in runs]

        if len(runs) < window * 2:
            output.append(
                ConvergenceResult(
                    command=cmd,
                    sizes=sizes,
                    means=means,
                    delta_pct=None,
                    converged=False,
                    window=window,
                )
            )
            continue

        first_mean = sum(means[:window]) / window
        last_mean = sum(means[-window:]) / window
        if first_mean == 0:
            delta_pct = None
            converged = False
        else:
            delta_pct = abs(last_mean - first_mean) / first_mean * 100.0
            converged = delta_pct < threshold_pct

        output.append(
            ConvergenceResult(
                command=cmd,
                sizes=sizes,
                means=means,
                delta_pct=delta_pct,
                converged=converged,
                window=window,
            )
        )

    output.sort(key=lambda r: r.command)
    return output


def render_convergence_table(rows: List[ConvergenceResult]) -> str:
    if not rows:
        return "No convergence data."
    header = f"{'Command':<30} {'Sizes':>6} {'First Mean':>12} {'Last Mean':>12} {'Delta%':>8} {'Converged':>10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        first = sum(r.means[: r.window]) / r.window if len(r.means) >= r.window else float("nan")
        last = sum(r.means[-r.window :]) / r.window if len(r.means) >= r.window else float("nan")
        delta = f"{r.delta_pct:.2f}" if r.delta_pct is not None else "N/A"
        conv = "yes" if r.converged else "no"
        lines.append(
            f"{r.command:<30} {len(r.sizes):>6} {first:>12.4f} {last:>12.4f} {delta:>8} {conv:>10}"
        )
    return "\n".join(lines)
