"""Inflection point detection for benchmark results.

An inflection point is a size at which the rate of change in runtime
switches direction — e.g. from decelerating to accelerating growth.
This is useful for identifying where algorithmic complexity changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


@dataclass
class InflectionPoint:
    """A detected inflection point for a single command."""

    command: str
    size: int
    mean_before: float   # average slope before the inflection
    mean_after: float    # average slope after the inflection
    direction: str       # "accelerating" or "decelerating"


def _slopes(sizes: List[int], times: List[float]) -> List[float]:
    """Compute finite differences (slopes) between consecutive points."""
    slopes = []
    for i in range(1, len(sizes)):
        dx = sizes[i] - sizes[i - 1]
        dy = times[i] - times[i - 1]
        slopes.append(dy / dx if dx != 0 else 0.0)
    return slopes


def detect_inflections(
    results: List[BenchmarkResult],
    min_points: int = 4,
) -> List[InflectionPoint]:
    """Detect inflection points in benchmark results per command.

    For each command, sizes are sorted and the slope between consecutive
    (size, mean_time) pairs is computed.  An inflection is reported at
    the size where the slope sequence changes from decreasing to
    increasing (decelerating → accelerating) or vice-versa.

    Args:
        results:    List of BenchmarkResult instances.
        min_points: Minimum number of successful data points required
                    per command to attempt detection (default 4).

    Returns:
        A list of InflectionPoint objects, one per detected inflection
        per command.  Commands with too few points are skipped.
    """
    # Group successful results by command
    groups: dict[str, dict[int, float]] = {}
    for r in results:
        if not r.success:
            continue
        groups.setdefault(r.command, {})
        groups[r.command][r.size] = r.mean

    inflections: List[InflectionPoint] = []

    for command, size_map in groups.items():
        if len(size_map) < min_points:
            continue

        sizes = sorted(size_map)
        times = [size_map[s] for s in sizes]
        slopes = _slopes(sizes, times)

        if len(slopes) < 2:
            continue

        # Detect sign changes in the second derivative (slope of slopes)
        for i in range(1, len(slopes)):
            prev_slope = slopes[i - 1]
            curr_slope = slopes[i]

            # Second derivative sign change
            second_deriv_prev = curr_slope - prev_slope
            if i < len(slopes) - 1:
                second_deriv_next = slopes[i + 1] - curr_slope
            else:
                continue  # need at least one point after to confirm

            if second_deriv_prev < 0 and second_deriv_next > 0:
                direction = "accelerating"
                mean_before = sum(slopes[:i]) / i
                mean_after = sum(slopes[i:]) / len(slopes[i:])
                inflections.append(
                    InflectionPoint(
                        command=command,
                        size=sizes[i],
                        mean_before=mean_before,
                        mean_after=mean_after,
                        direction=direction,
                    )
                )
            elif second_deriv_prev > 0 and second_deriv_next < 0:
                direction = "decelerating"
                mean_before = sum(slopes[:i]) / i
                mean_after = sum(slopes[i:]) / len(slopes[i:])
                inflections.append(
                    InflectionPoint(
                        command=command,
                        size=sizes[i],
                        mean_before=mean_before,
                        mean_after=mean_after,
                        direction=direction,
                    )
                )

    return inflections


def render_inflection_table(inflections: List[InflectionPoint]) -> str:
    """Render inflection points as a plain-text table."""
    if not inflections:
        return "No inflection points detected."

    header = f"{'Command':<30} {'Size':>10} {'Slope Before':>14} {'Slope After':>13} {'Direction':<14}"
    sep = "-" * len(header)
    rows = [header, sep]

    for pt in inflections:
        rows.append(
            f"{pt.command:<30} {pt.size:>10} "
            f"{pt.mean_before:>14.6f} {pt.mean_after:>13.6f} "
            f"{pt.direction:<14}"
        )

    return "\n".join(rows)
