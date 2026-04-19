"""Comparison utilities for benchmark results across commands or runs."""

from dataclasses import dataclass
from typing import List, Dict
from batchmark.runner import BenchmarkResult, mean, median, stdev


@dataclass
class ComparisonRow:
    label: str
    size: int
    mean: float
    median: float
    stdev: float
    min: float
    max: float
    relative: float  # ratio vs baseline (first command)


def compare_results(
    groups: Dict[str, List[BenchmarkResult]]
) -> Dict[int, List[ComparisonRow]]:
    """
    Given a dict mapping command label -> list of BenchmarkResult,
    return a dict mapping input_size -> list of ComparisonRow (one per label).
    Relative speed is normalized to the first label's mean.
    """
    if not groups:
        return {}

    sizes: set = set()
    for results in groups.values():
        for r in results:
            sizes.add(r.input_size)

    comparison: Dict[int, List[ComparisonRow]] = {}

    for size in sorted(sizes):
        rows: List[ComparisonRow] = []
        baseline_mean: float | None = None

        for label, results in groups.items():
            matched = [r for r in results if r.input_size == size and r.exit_code == 0]
            if not matched:
                continue
            times = [r.elapsed for r in matched]
            m = mean(times)
            if baseline_mean is None:
                baseline_mean = m
            relative = m / baseline_mean if baseline_mean else 1.0
            rows.append(ComparisonRow(
                label=label,
                size=size,
                mean=m,
                median=median(times),
                stdev=stdev(times),
                min=min(times),
                max=max(times),
                relative=relative,
            ))

        comparison[size] = rows

    return comparison


def render_comparison_table(comparison: Dict[int, List[ComparisonRow]]) -> str:
    header = f"{'Size':>10}  {'Label':<24}  {'Mean':>8}  {'Median':>8}  {'Stdev':>8}  {'Rel':>6}"
    sep = "-" * len(header)
    lines = [header, sep]
    for size in sorted(comparison):
        for row in comparison[size]:
            lines.append(
                f"{row.size:>10}  {row.label:<24}  {row.mean:>8.4f}  "
                f"{row.median:>8.4f}  {row.stdev:>8.4f}  {row.relative:>6.2f}x"
            )
        lines.append("")
    return "\n".join(lines)
