"""Variance analysis: compute coefficient of variation and stability rating per command."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean, stdev


@dataclass
class VarianceResult:
    command: str
    sample_count: int
    mean_time: float
    stdev_time: float
    cv_percent: float          # coefficient of variation as a percentage
    stability: str             # "stable", "moderate", "unstable"
    min_time: float
    max_time: float


def _stability_label(cv: float) -> str:
    if cv < 5.0:
        return "stable"
    elif cv < 20.0:
        return "moderate"
    else:
        return "unstable"


def analyze_variance(
    results: List[BenchmarkResult],
    command_filter: Optional[str] = None,
) -> List[VarianceResult]:
    """Group successful results by command and compute variance stats."""
    from batchmark.filter import group_by_command

    successful = [r for r in results if r.exit_code == 0 and r.elapsed is not None]
    if command_filter:
        successful = [r for r in successful if r.command == command_filter]

    groups = group_by_command(successful)
    output: List[VarianceResult] = []

    for cmd, group in sorted(groups.items()):
        times = [r.elapsed for r in group if r.elapsed is not None]
        if len(times) < 2:
            continue
        m = mean(times)
        s = stdev(times)
        cv = (s / m * 100.0) if m > 0 else 0.0
        output.append(VarianceResult(
            command=cmd,
            sample_count=len(times),
            mean_time=round(m, 4),
            stdev_time=round(s, 4),
            cv_percent=round(cv, 2),
            stability=_stability_label(cv),
            min_time=round(min(times), 4),
            max_time=round(max(times), 4),
        ))

    return output


def render_variance_table(rows: List[VarianceResult]) -> str:
    if not rows:
        return "No variance data available."

    header = f"{'Command':<30} {'N':>4} {'Mean':>10} {'Stdev':>10} {'CV%':>8} {'Min':>10} {'Max':>10} {'Stability':<10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"{r.command:<30} {r.sample_count:>4} {r.mean_time:>10.4f} "
            f"{r.stdev_time:>10.4f} {r.cv_percent:>8.2f} "
            f"{r.min_time:>10.4f} {r.max_time:>10.4f} {r.stability:<10}"
        )
    return "\n".join(lines)
