"""Cadence analysis: measure how consistently a command's runtime grows
between successive input sizes (coefficient of variation of step ratios)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from batchmark.runner import BenchmarkResult


@dataclass
class CadenceResult:
    command: str
    ratios: List[float]          # successive mean[i+1]/mean[i]
    mean_ratio: float            # average step ratio
    cv: float                    # coefficient of variation of ratios
    label: str                   # "steady" / "irregular" / "erratic"


def _label(cv: float) -> str:
    if cv < 0.10:
        return "steady"
    if cv < 0.30:
        return "irregular"
    return "erratic"


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _stdev(values: List[float], mu: float) -> float:
    if len(values) < 2:
        return 0.0
    return (sum((v - mu) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def analyze_cadence(
    results: List[BenchmarkResult],
    command: str | None = None,
) -> List[CadenceResult]:
    """Return one CadenceResult per command found in *results*."""
    # group successful results by command -> sorted list of (size, mean)
    groups: Dict[str, Dict[int, List[float]]] = {}
    for r in results:
        if not r.success:
            continue
        if command and r.command != command:
            continue
        groups.setdefault(r.command, {}).setdefault(r.size, []).append(r.mean)

    output: List[CadenceResult] = []
    for cmd, size_map in groups.items():
        sizes = sorted(size_map)
        if len(sizes) < 2:
            continue
        means = [_mean(size_map[s]) for s in sizes]
        ratios = [
            means[i + 1] / means[i]
            for i in range(len(means) - 1)
            if means[i] > 0
        ]
        if not ratios:
            continue
        mu = _mean(ratios)
        cv = _stdev(ratios, mu) / mu if mu > 0 else 0.0
        output.append(CadenceResult(command=cmd, ratios=ratios,
                                    mean_ratio=mu, cv=cv, label=_label(cv)))
    output.sort(key=lambda r: r.command)
    return output


def render_cadence_table(rows: List[CadenceResult]) -> str:
    if not rows:
        return "No cadence data available."
    header = f"{'Command':<30} {'Steps':>5} {'MeanRatio':>10} {'CV':>8} {'Label':<10}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"{r.command:<30} {len(r.ratios):>5} "
            f"{r.mean_ratio:>10.4f} {r.cv:>8.4f} {r.label:<10}"
        )
    return "\n".join(lines)
