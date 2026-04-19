from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean, stdev


@dataclass
class OutlierResult:
    result: BenchmarkResult
    z_score: float
    is_outlier: bool


def detect_outliers(
    results: List[BenchmarkResult],
    threshold: float = 2.0,
) -> List[OutlierResult]:
    """Flag results whose mean time z-score exceeds threshold."""
    successful = [r for r in results if r.success and r.times]
    if len(successful) < 2:
        return [
            OutlierResult(result=r, z_score=0.0, is_outlier=False)
            for r in results
        ]

    means = [mean(r.times) for r in successful]
    mu = mean(means)
    sd = stdev(means)

    annotated = []
    for r in results:
        if not r.success or not r.times:
            annotated.append(OutlierResult(result=r, z_score=0.0, is_outlier=False))
            continue
        z = abs(mean(r.times) - mu) / sd if sd > 0 else 0.0
        annotated.append(OutlierResult(result=r, z_score=round(z, 4), is_outlier=z > threshold))
    return annotated


def render_outlier_table(outliers: List[OutlierResult]) -> str:
    header = f"{'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Z-Score':>8} {'Outlier':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for o in outliers:
        r = o.result
        m = mean(r.times) if r.times else float("nan")
        flag = "YES" if o.is_outlier else ""
        rows.append(
            f"{r.command:<30} {r.size:>8} {m:>10.4f} {o.z_score:>8.4f} {flag:>8}"
        )
    return "\n".join(rows)
