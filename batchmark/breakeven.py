"""Breakeven analysis: find the input size where one command overtakes another."""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from batchmark.runner import BenchmarkResult


@dataclass
class BreakevenResult:
    command_a: str
    command_b: str
    breakeven_size: Optional[float]  # None if no crossover found
    a_wins_below: bool  # True if command_a is faster below breakeven
    sizes_a: List[int]
    times_a: List[float]
    sizes_b: List[int]
    times_b: List[float]


def _interpolate_crossover(
    sizes_a: List[int], times_a: List[float],
    sizes_b: List[int], times_b: List[float],
) -> Optional[float]:
    """Linear interpolation to find where two series cross."""
    common = sorted(set(sizes_a) & set(sizes_b))
    if len(common) < 2:
        return None
    ta = {s: t for s, t in zip(sizes_a, times_a)}
    tb = {s: t for s, t in zip(sizes_b, times_b)}
    diffs = [(s, ta[s] - tb[s]) for s in common]
    for i in range(len(diffs) - 1):
        s1, d1 = diffs[i]
        s2, d2 = diffs[i + 1]
        if d1 * d2 < 0:  # sign change => crossover
            # linear interpolation
            frac = d1 / (d1 - d2)
            return s1 + frac * (s2 - s1)
        if d1 == 0:
            return float(s1)
    return None


def find_breakeven(
    results: List[BenchmarkResult],
    command_a: str,
    command_b: str,
) -> BreakevenResult:
    def _collect(cmd: str) -> Tuple[List[int], List[float]]:
        rows = sorted(
            [r for r in results if r.command == cmd and r.success],
            key=lambda r: r.size,
        )
        return [r.size for r in rows], [r.mean for r in rows]

    sizes_a, times_a = _collect(command_a)
    sizes_b, times_b = _collect(command_b)
    crossover = _interpolate_crossover(sizes_a, times_a, sizes_b, times_b)
    # determine which command wins below breakeven (or overall if no crossover)
    common = sorted(set(sizes_a) & set(sizes_b))
    a_wins_below = True
    if common:
        ta = {s: t for s, t in zip(sizes_a, times_a)}
        tb = {s: t for s, t in zip(sizes_b, times_b)}
        a_wins_below = ta[common[0]] < tb[common[0]]
    return BreakevenResult(
        command_a=command_a,
        command_b=command_b,
        breakeven_size=crossover,
        a_wins_below=a_wins_below,
        sizes_a=sizes_a,
        times_a=times_a,
        sizes_b=sizes_b,
        times_b=times_b,
    )


def render_breakeven_table(result: BreakevenResult) -> str:
    lines = [
        f"Breakeven: {result.command_a!r} vs {result.command_b!r}",
        "-" * 52,
    ]
    if result.breakeven_size is None:
        winner = result.command_a if result.a_wins_below else result.command_b
        lines.append(f"  No crossover found. {winner!r} is consistently faster.")
    else:
        faster_below = result.command_a if result.a_wins_below else result.command_b
        faster_above = result.command_b if result.a_wins_below else result.command_a
        lines.append(f"  Crossover at size ≈ {result.breakeven_size:.1f}")
        lines.append(f"  {faster_below!r} faster below, {faster_above!r} faster above")
    lines.append("")
    header = f"  {'size':>8}  {'cmd_a (s)':>12}  {'cmd_b (s)':>12}  {'faster':>10}"
    lines.append(header)
    ta = dict(zip(result.sizes_a, result.times_a))
    tb = dict(zip(result.sizes_b, result.times_b))
    for s in sorted(set(result.sizes_a) & set(result.sizes_b)):
        a, b = ta[s], tb[s]
        faster = result.command_a if a < b else result.command_b
        lines.append(f"  {s:>8}  {a:>12.4f}  {b:>12.4f}  {faster:>10}")
    return "\n".join(lines)
