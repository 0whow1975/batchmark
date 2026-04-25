"""Detect saturation points where performance gains diminish with increasing input size."""
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class SaturationResult:
    command: str
    saturation_size: Optional[int]   # input size where saturation begins
    pre_slope: float                  # avg time-per-unit before saturation
    post_slope: float                 # avg time-per-unit after saturation
    ratio: float                      # post_slope / pre_slope  (<1 means slowing growth)
    saturated: bool


def _slope(xs: List[int], ys: List[float]) -> float:
    """Simple rise-over-run slope between first and last point."""
    if len(xs) < 2 or xs[-1] == xs[0]:
        return 0.0
    return (ys[-1] - ys[0]) / (xs[-1] - xs[0])


def detect_saturation(
    results: List[BenchmarkResult],
    threshold: float = 0.5,
    min_points: int = 4,
) -> List[SaturationResult]:
    """Detect commands whose growth rate drops by *threshold* fraction or more.

    A command is considered saturated when the slope in the second half of its
    size range is less than (1 - threshold) times the slope in the first half.
    """
    from batchmark.filter import group_by_command

    groups = group_by_command([r for r in results if r.success])
    out: List[SaturationResult] = []

    for cmd, rows in groups.items():
        rows_sorted = sorted(rows, key=lambda r: r.size)
        if len(rows_sorted) < min_points:
            continue

        mid = len(rows_sorted) // 2
        first_half = rows_sorted[:mid]
        second_half = rows_sorted[mid:]

        xs1 = [r.size for r in first_half]
        ys1 = [r.mean_time for r in first_half]
        xs2 = [r.size for r in second_half]
        ys2 = [r.mean_time for r in second_half]

        s1 = _slope(xs1, ys1)
        s2 = _slope(xs2, ys2)

        if s1 <= 0:
            ratio = 1.0
        else:
            ratio = s2 / s1

        saturated = ratio < (1.0 - threshold)
        sat_size = rows_sorted[mid].size if saturated else None

        out.append(SaturationResult(
            command=cmd,
            saturation_size=sat_size,
            pre_slope=s1,
            post_slope=s2,
            ratio=ratio,
            saturated=saturated,
        ))

    return out


def render_saturation_table(rows: List[SaturationResult]) -> str:
    if not rows:
        return "No saturation data."
    header = f"{'Command':<30} {'Sat.Size':>10} {'PreSlope':>12} {'PostSlope':>12} {'Ratio':>8} {'Saturated':>10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        sat_size = str(r.saturation_size) if r.saturation_size is not None else "N/A"
        lines.append(
            f"{r.command:<30} {sat_size:>10} {r.pre_slope:>12.6f} {r.post_slope:>12.6f}"
            f" {r.ratio:>8.3f} {'YES' if r.saturated else 'no':>10}"
        )
    return "\n".join(lines)
