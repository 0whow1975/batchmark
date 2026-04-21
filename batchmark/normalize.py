"""Normalize benchmark results relative to a reference command or size."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean


@dataclass
class NormalizedResult:
    command: str
    size: int
    raw_mean: float
    reference_mean: float
    ratio: float          # raw_mean / reference_mean
    pct_change: float     # (ratio - 1) * 100
    faster: bool          # True if this command is faster than reference


def normalize_results(
    results: List[BenchmarkResult],
    reference_command: str,
) -> List[NormalizedResult]:
    """Normalize all results against the mean time of *reference_command* at each size."""
    # Build a lookup: size -> mean time for the reference command
    ref_times: dict = {}
    for r in results:
        if r.command == reference_command and not r.error:
            times = [t for t in r.times if t is not None]
            if times:
                ref_times[r.size] = mean(times)

    normalized: List[NormalizedResult] = []
    for r in results:
        if r.error or r.size not in ref_times:
            continue
        times = [t for t in r.times if t is not None]
        if not times:
            continue
        raw = mean(times)
        ref = ref_times[r.size]
        ratio = raw / ref if ref > 0 else float("inf")
        normalized.append(
            NormalizedResult(
                command=r.command,
                size=r.size,
                raw_mean=raw,
                reference_mean=ref,
                ratio=ratio,
                pct_change=(ratio - 1.0) * 100.0,
                faster=ratio < 1.0,
            )
        )
    return normalized


def render_normalize_table(rows: List[NormalizedResult], reference: str) -> str:
    """Render a plain-text table of normalized results."""
    if not rows:
        return "No normalized results to display."

    header = f"{'Command':<30} {'Size':>10} {'Mean(s)':>10} {'Ref(s)':>10} {'Ratio':>8} {'Δ%':>8} {'Faster?':>8}"
    sep = "-" * len(header)
    lines = [
        f"Reference command: {reference}",
        sep,
        header,
        sep,
    ]
    for row in rows:
        faster_str = "yes" if row.faster else "no"
        sign = "+" if row.pct_change >= 0 else ""
        lines.append(
            f"{row.command:<30} {row.size:>10} {row.raw_mean:>10.4f} "
            f"{row.reference_mean:>10.4f} {row.ratio:>8.3f} "
            f"{sign}{row.pct_change:>7.1f}% {faster_str:>8}"
        )
    lines.append(sep)
    return "\n".join(lines)
