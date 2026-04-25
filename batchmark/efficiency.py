"""Compute efficiency scores: performance per unit size."""
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class EfficiencyRow:
    command: str
    size: int
    mean_time: float
    efficiency: Optional[float]  # size / mean_time; None if failed or zero time
    rank: int


def compute_efficiency(
    results: List[BenchmarkResult],
    command: Optional[str] = None,
) -> List[EfficiencyRow]:
    """Compute efficiency (size / mean_time) for each (command, size) pair.

    Higher efficiency means more work done per unit time.
    Results are sorted descending by efficiency (failures last).
    """
    filtered = [r for r in results if command is None or r.command == command]

    rows: List[EfficiencyRow] = []
    for r in filtered:
        if not r.success or r.mean is None or r.mean <= 0:
            rows.append(EfficiencyRow(
                command=r.command,
                size=r.size,
                mean_time=r.mean if r.mean is not None else float("nan"),
                efficiency=None,
                rank=0,
            ))
        else:
            rows.append(EfficiencyRow(
                command=r.command,
                size=r.size,
                mean_time=r.mean,
                efficiency=r.size / r.mean,
                rank=0,
            ))

    # Sort: valid rows descending by efficiency, then failures
    valid = sorted([row for row in rows if row.efficiency is not None],
                   key=lambda x: x.efficiency, reverse=True)
    invalid = [row for row in rows if row.efficiency is None]

    for i, row in enumerate(valid, start=1):
        row.rank = i
    for i, row in enumerate(invalid, start=len(valid) + 1):
        row.rank = i

    return valid + invalid


def render_efficiency_table(rows: List[EfficiencyRow]) -> str:
    """Render efficiency rows as a plain-text table."""
    if not rows:
        return "No efficiency data."

    header = f"{'Rank':>4}  {'Command':<20}  {'Size':>8}  {'Mean(s)':>10}  {'Efficiency':>12}"
    sep = "-" * len(header)
    lines = [header, sep]
    for row in rows:
        eff = f"{row.efficiency:.4f}" if row.efficiency is not None else "N/A"
        lines.append(
            f"{row.rank:>4}  {row.command:<20}  {row.size:>8}  "
            f"{row.mean_time:>10.4f}  {eff:>12}"
        )
    return "\n".join(lines)
