"""Win-rate analysis: for each pair of commands, count how often each wins across input sizes."""
from dataclasses import dataclass
from typing import List, Dict, Tuple
from batchmark.runner import BenchmarkResult


@dataclass
class WinRateRow:
    command_a: str
    command_b: str
    wins_a: int
    wins_b: int
    ties: int
    total: int
    win_rate_a: float  # fraction 0..1
    win_rate_b: float


def _pairs(commands: List[str]) -> List[Tuple[str, str]]:
    pairs = []
    for i in range(len(commands)):
        for j in range(i + 1, len(commands)):
            pairs.append((commands[i], commands[j]))
    return pairs


def compute_win_rates(results: List[BenchmarkResult]) -> List[WinRateRow]:
    """Compare every pair of commands across shared input sizes."""
    # Group successful results by (command, size)
    by_key: Dict[Tuple[str, int], float] = {}
    commands = []
    for r in results:
        if not r.success:
            continue
        if r.command not in commands:
            commands.append(r.command)
        by_key[(r.command, r.size)] = r.mean_time

    rows: List[WinRateRow] = []
    for cmd_a, cmd_b in _pairs(commands):
        wins_a = wins_b = ties = 0
        sizes_a = {s for (c, s) in by_key if c == cmd_a}
        sizes_b = {s for (c, s) in by_key if c == cmd_b}
        shared = sizes_a & sizes_b
        for size in shared:
            t_a = by_key[(cmd_a, size)]
            t_b = by_key[(cmd_b, size)]
            if t_a < t_b:
                wins_a += 1
            elif t_b < t_a:
                wins_b += 1
            else:
                ties += 1
        total = wins_a + wins_b + ties
        win_rate_a = wins_a / total if total else 0.0
        win_rate_b = wins_b / total if total else 0.0
        rows.append(WinRateRow(cmd_a, cmd_b, wins_a, wins_b, ties, total, win_rate_a, win_rate_b))
    return rows


def render_winrate_table(rows: List[WinRateRow]) -> str:
    if not rows:
        return "No win-rate data available."
    header = f"{'Command A':<30} {'Command B':<30} {'Wins A':>6} {'Wins B':>6} {'Ties':>5} {'WR-A':>7} {'WR-B':>7}"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"{r.command_a:<30} {r.command_b:<30} {r.wins_a:>6} {r.wins_b:>6} {r.ties:>5} {r.win_rate_a:>7.1%} {r.win_rate_b:>7.1%}"
        )
    return "\n".join(lines)
