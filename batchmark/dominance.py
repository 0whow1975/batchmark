"""Dominance analysis: find commands that are strictly better than others across all sizes."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class DominanceRow:
    winner: str
    loser: str
    sizes_compared: int
    max_speedup: float
    min_speedup: float
    avg_speedup: float
    strict: bool  # True if winner is faster at every shared size


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_dominance(
    results: List[BenchmarkResult],
    command_filter: Optional[List[str]] = None,
) -> List[DominanceRow]:
    """Return rows where one command dominates another across all shared sizes."""
    from collections import defaultdict

    by_cmd: dict = defaultdict(dict)
    for r in results:
        if not r.success:
            continue
        if command_filter and r.command not in command_filter:
            continue
        by_cmd[r.command][r.input_size] = r.mean_time

    commands = list(by_cmd.keys())
    rows: List[DominanceRow] = []

    for i, cmd_a in enumerate(commands):
        for cmd_b in commands[i + 1:]:
            sizes_a = set(by_cmd[cmd_a].keys())
            sizes_b = set(by_cmd[cmd_b].keys())
            shared = sorted(sizes_a & sizes_b)
            if not shared:
                continue

            ratios_ab = [by_cmd[cmd_b][s] / by_cmd[cmd_a][s] for s in shared]
            ratios_ba = [by_cmd[cmd_a][s] / by_cmd[cmd_b][s] for s in shared]

            for winner, loser, ratios in [
                (cmd_a, cmd_b, ratios_ab),
                (cmd_b, cmd_a, ratios_ba),
            ]:
                if all(r >= 1.0 for r in ratios):
                    rows.append(
                        DominanceRow(
                            winner=winner,
                            loser=loser,
                            sizes_compared=len(shared),
                            max_speedup=max(ratios),
                            min_speedup=min(ratios),
                            avg_speedup=_mean(ratios),
                            strict=all(r > 1.0 for r in ratios),
                        )
                    )
                    break

    rows.sort(key=lambda r: -r.avg_speedup)
    return rows


def render_dominance_table(rows: List[DominanceRow]) -> str:
    if not rows:
        return "No dominance relationships found."
    header = f"{'Winner':<20} {'Loser':<20} {'Sizes':>5} {'Min Speedup':>12} {'Max Speedup':>12} {'Avg Speedup':>12} {'Strict':>7}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        strict_str = "yes" if r.strict else "no"
        lines.append(
            f"{r.winner:<20} {r.loser:<20} {r.sizes_compared:>5}"
            f" {r.min_speedup:>12.3f} {r.max_speedup:>12.3f} {r.avg_speedup:>12.3f} {strict_str:>7}"
        )
    return "\n".join(lines)
