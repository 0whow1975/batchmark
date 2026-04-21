"""Re-rank benchmark results by a chosen metric and emit an ordered report."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from batchmark.runner import BenchmarkResult


VALID_METRICS = ("mean", "median", "min", "max", "stdev")


@dataclass
class RerankRow:
    rank: int
    command: str
    size: int
    metric: str
    value: float
    runs: int


def rerank_results(
    results: List[BenchmarkResult],
    metric: str = "mean",
    ascending: bool = True,
    top_n: Optional[int] = None,
) -> List[RerankRow]:
    """Sort *successful* results by *metric* and return ranked rows."""
    if metric not in VALID_METRICS:
        raise ValueError(f"metric must be one of {VALID_METRICS}, got {metric!r}")

    rows: List[RerankRow] = []
    for r in results:
        if not r.success or not r.times:
            continue
        value = getattr(r, metric)
        rows.append(
            RerankRow(
                rank=0,
                command=r.command,
                size=r.size,
                metric=metric,
                value=value,
                runs=len(r.times),
            )
        )

    rows.sort(key=lambda row: row.value, reverse=not ascending)

    for i, row in enumerate(rows, start=1):
        row.rank = i

    if top_n is not None:
        rows = rows[:top_n]

    return rows


def render_rerank_table(rows: List[RerankRow]) -> str:
    """Render ranked rows as a plain-text table."""
    if not rows:
        return "No results to rank."

    header = f"{'Rank':>4}  {'Command':<30}  {'Size':>8}  {'Metric':<8}  {'Value':>10}  {'Runs':>4}"
    sep = "-" * len(header)
    lines = [header, sep]
    for row in rows:
        lines.append(
            f"{row.rank:>4}  {row.command:<30}  {row.size:>8}  "
            f"{row.metric:<8}  {row.value:>10.4f}  {row.runs:>4}"
        )
    return "\n".join(lines)
