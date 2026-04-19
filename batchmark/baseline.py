"""Baseline comparison: compare current results against a saved baseline."""

from dataclasses import dataclass
from typing import List, Optional, Dict
from batchmark.runner import BenchmarkResult
from batchmark.history import save_results, load_results


@dataclass
class BaselineDiff:
    command: str
    size: int
    baseline_mean: float
    current_mean: float
    delta: float        # absolute difference
    pct_change: float  # percentage change vs baseline
    regression: bool   # True if current is slower by threshold


def set_baseline(results: List[BenchmarkResult], path: str, tag: str = "baseline") -> None:
    """Save results as a named baseline to a JSON history file."""
    save_results(results, path, tag=tag)


def load_baseline(path: str, tag: str = "baseline") -> List[BenchmarkResult]:
    """Load baseline results from history file by tag."""
    return load_results(path, tag=tag)


def diff_against_baseline(
    baseline: List[BenchmarkResult],
    current: List[BenchmarkResult],
    regression_threshold: float = 0.10,
) -> List[BaselineDiff]:
    """Compare current results against baseline; flag regressions."""
    index: Dict[tuple, BenchmarkResult] = {
        (r.command, r.size): r for r in baseline if r.success
    }
    diffs: List[BaselineDiff] = []
    for r in current:
        if not r.success:
            continue
        key = (r.command, r.size)
        b = index.get(key)
        if b is None:
            continue
        delta = r.mean - b.mean
        pct = delta / b.mean if b.mean else 0.0
        diffs.append(BaselineDiff(
            command=r.command,
            size=r.size,
            baseline_mean=b.mean,
            current_mean=r.mean,
            delta=delta,
            pct_change=pct,
            regression=pct > regression_threshold,
        ))
    return diffs


def render_baseline_table(diffs: List[BaselineDiff]) -> str:
    """Render baseline diff as a plain-text table."""
    if not diffs:
        return "No comparable results found."
    header = f"{'Command':<30} {'Size':>8} {'Baseline':>10} {'Current':>10} {'Delta':>10} {'Change':>8} {'Regress':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for d in diffs:
        flag = "YES" if d.regression else ""
        rows.append(
            f"{d.command:<30} {d.size:>8} {d.baseline_mean:>10.4f} {d.current_mean:>10.4f}"
            f" {d.delta:>+10.4f} {d.pct_change:>+7.1%} {flag:>8}"
        )
    return "\n".join(rows)
