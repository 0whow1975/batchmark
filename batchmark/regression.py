from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class RegressionResult:
    command: str
    size: int
    baseline_mean: float
    current_mean: float
    delta: float
    pct_change: float
    is_regression: bool


def detect_regressions(
    baseline: List[BenchmarkResult],
    current: List[BenchmarkResult],
    threshold: float = 0.10,
) -> List[RegressionResult]:
    """Compare current results against baseline, flagging regressions."""
    baseline_map = {
        (r.command, r.size): r
        for r in baseline
        if r.exit_code == 0 and r.times
    }
    results = []
    for r in current:
        if r.exit_code != 0 or not r.times:
            continue
        key = (r.command, r.size)
        b = baseline_map.get(key)
        if b is None:
            continue
        b_mean = sum(b.times) / len(b.times)
        c_mean = sum(r.times) / len(r.times)
        delta = c_mean - b_mean
        pct = delta / b_mean if b_mean > 0 else 0.0
        results.append(RegressionResult(
            command=r.command,
            size=r.size,
            baseline_mean=b_mean,
            current_mean=c_mean,
            delta=delta,
            pct_change=pct,
            is_regression=pct > threshold,
        ))
    return results


def render_regression_table(rows: List[RegressionResult]) -> str:
    if not rows:
        return "No comparable results found."
    header = f"{'Command':<30} {'Size':>8} {'Baseline':>10} {'Current':>10} {'Delta':>10} {'Change':>8} {'Flag':>6}"
    lines = [header, "-" * len(header)]
    for r in rows:
        flag = "REGR" if r.is_regression else "ok"
        lines.append(
            f"{r.command:<30} {r.size:>8} {r.baseline_mean:>10.4f} "
            f"{r.current_mean:>10.4f} {r.delta:>+10.4f} "
            f"{r.pct_change:>7.1%} {flag:>6}"
        )
    return "\n".join(lines)
