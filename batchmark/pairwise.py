"""Pairwise comparison of benchmark results across two commands."""
from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class PairwiseRow:
    size: int
    command_a: str
    command_b: str
    mean_a: float
    mean_b: float
    delta: float        # mean_b - mean_a
    ratio: float        # mean_b / mean_a  (>1 means b is slower)
    winner: str         # "a", "b", or "tie"


def compare_pair(
    results: List[BenchmarkResult],
    command_a: str,
    command_b: str,
    tie_threshold: float = 0.02,
) -> List[PairwiseRow]:
    """Compare two commands head-to-head across shared input sizes."""
    a_map = {
        r.size: r
        for r in results
        if r.command == command_a and not r.error and r.times
    }
    b_map = {
        r.size: r
        for r in results
        if r.command == command_b and not r.error and r.times
    }
    shared_sizes = sorted(set(a_map) & set(b_map))
    rows: List[PairwiseRow] = []
    for size in shared_sizes:
        ra = a_map[size]
        rb = b_map[size]
        ma = sum(ra.times) / len(ra.times)
        mb = sum(rb.times) / len(rb.times)
        delta = mb - ma
        ratio = mb / ma if ma > 0 else float("inf")
        if abs(ratio - 1.0) <= tie_threshold:
            winner = "tie"
        elif ma < mb:
            winner = "a"
        else:
            winner = "b"
        rows.append(
            PairwiseRow(
                size=size,
                command_a=command_a,
                command_b=command_b,
                mean_a=ma,
                mean_b=mb,
                delta=delta,
                ratio=ratio,
                winner=winner,
            )
        )
    return rows


def render_pairwise_table(rows: List[PairwiseRow]) -> str:
    if not rows:
        return "No pairwise data available."
    cmd_a = rows[0].command_a
    cmd_b = rows[0].command_b
    header = f"{'Size':>10}  {'Mean A':>10}  {'Mean B':>10}  {'Delta':>10}  {'Ratio':>7}  Winner"
    sep = "-" * len(header)
    lines = [f"A: {cmd_a}  vs  B: {cmd_b}", sep, header, sep]
    for r in rows:
        winner_label = {"a": cmd_a, "b": cmd_b, "tie": "tie"}[r.winner]
        lines.append(
            f"{r.size:>10}  {r.mean_a:>10.4f}  {r.mean_b:>10.4f}"
            f"  {r.delta:>+10.4f}  {r.ratio:>7.3f}  {winner_label}"
        )
    lines.append(sep)
    wins_a = sum(1 for r in rows if r.winner == "a")
    wins_b = sum(1 for r in rows if r.winner == "b")
    ties = sum(1 for r in rows if r.winner == "tie")
    lines.append(f"Summary: {cmd_a} wins={wins_a}  {cmd_b} wins={wins_b}  ties={ties}")
    return "\n".join(lines)
