"""Filter and query BenchmarkResult collections."""

from typing import List, Optional, Callable
from batchmark.runner import BenchmarkResult


def filter_results(
    results: List[BenchmarkResult],
    *,
    command: Optional[str] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    success_only: bool = False,
    predicate: Optional[Callable[[BenchmarkResult], bool]] = None,
) -> List[BenchmarkResult]:
    """Return results matching all specified criteria."""
    out = []
    for r in results:
        if command is not None and r.command != command:
            continue
        if min_size is not None and r.input_size < min_size:
            continue
        if max_size is not None and r.input_size > max_size:
            continue
        if success_only and not r.success:
            continue
        if predicate is not None and not predicate(r):
            continue
        out.append(r)
    return out


def group_by_command(
    results: List[BenchmarkResult],
) -> dict[str, List[BenchmarkResult]]:
    """Group results by command string."""
    groups: dict[str, List[BenchmarkResult]] = {}
    for r in results:
        groups.setdefault(r.command, []).append(r)
    return groups


def group_by_size(
    results: List[BenchmarkResult],
) -> dict[int, List[BenchmarkResult]]:
    """Group results by input_size."""
    groups: dict[int, List[BenchmarkResult]] = {}
    for r in results:
        groups.setdefault(r.input_size, []).append(r)
    return groups


def top_n(
    results: List[BenchmarkResult],
    n: int,
    key: str = "mean",
    ascending: bool = True,
) -> List[BenchmarkResult]:
    """Return top-n results sorted by a stat key (mean/median/min/max)."""
    valid = [r for r in results if r.success and r.times]
    stat_map = {
        "mean": lambda r: sum(r.times) / len(r.times),
        "median": lambda r: sorted(r.times)[len(r.times) // 2],
        "min": lambda r: min(r.times),
        "max": lambda r: max(r.times),
    }
    if key not in stat_map:
        raise ValueError(f"Unknown key '{key}'. Choose from {list(stat_map)}.")
    return sorted(valid, key=stat_map[key], reverse=not ascending)[:n]
