"""Scaling analysis: fit timing data to O(n), O(n log n), O(n^2) models."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class ScalingResult:
    command: str
    best_fit: str          # e.g. "O(n)", "O(n log n)", "O(n^2)"
    r_squared: float       # goodness of fit for best model
    coefficients: dict     # {model_name: r_squared}


def _safe_log(x: float) -> float:
    return math.log(x) if x > 0 else 0.0


def _linear_regression(xs: List[float], ys: List[float]):
    """Return (slope, intercept, r_squared) for y ~ a*x + b."""
    n = len(xs)
    if n < 2:
        return 0.0, 0.0, 0.0
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0.0, sy / n, 0.0
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    y_mean = sy / n
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return slope, intercept, r2


def _fit_models(sizes: List[float], times: List[float]) -> dict:
    """Return r_squared for each candidate complexity model."""
    models = {}
    # O(n): y ~ n
    _, _, r2 = _linear_regression(sizes, times)
    models["O(n)"] = r2
    # O(n log n): y ~ n*log(n)
    xs_nlogn = [s * _safe_log(s) for s in sizes]
    _, _, r2 = _linear_regression(xs_nlogn, times)
    models["O(n log n)"] = r2
    # O(n^2): y ~ n^2
    xs_n2 = [s * s for s in sizes]
    _, _, r2 = _linear_regression(xs_n2, times)
    models["O(n^2)"] = r2
    # O(log n): y ~ log(n)
    xs_log = [_safe_log(s) for s in sizes]
    _, _, r2 = _linear_regression(xs_log, times)
    models["O(log n)"] = r2
    return models


def analyze_scaling(
    results: List[BenchmarkResult],
    command: Optional[str] = None,
) -> List[ScalingResult]:
    """Group successful results by command and fit scaling models."""
    from batchmark.filter import group_by_command

    grouped = group_by_command([r for r in results if r.success])
    if command:
        grouped = {k: v for k, v in grouped.items() if k == command}

    output: List[ScalingResult] = []
    for cmd, runs in grouped.items():
        runs_sorted = sorted(runs, key=lambda r: r.size)
        if len(runs_sorted) < 3:
            continue
        sizes = [float(r.size) for r in runs_sorted]
        times = [r.mean for r in runs_sorted]
        coefficients = _fit_models(sizes, times)
        best_fit = max(coefficients, key=lambda k: coefficients[k])
        output.append(
            ScalingResult(
                command=cmd,
                best_fit=best_fit,
                r_squared=coefficients[best_fit],
                coefficients=coefficients,
            )
        )
    return output


def render_scaling_table(results: List[ScalingResult]) -> str:
    if not results:
        return "No scaling data available."
    header = f"{'Command':<30} {'Best Fit':<14} {'R²':>6}"
    sep = "-" * len(header)
    rows = [header, sep]
    for r in results:
        rows.append(f"{r.command:<30} {r.best_fit:<14} {r.r_squared:>6.4f}")
    return "\n".join(rows)
