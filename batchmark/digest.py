"""Digest module: produce a concise summary digest of benchmark results."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean, median, stdev, min as bm_min


@dataclass
class DigestEntry:
    command: str
    sample_count: int
    mean_time: float
    median_time: float
    stdev_time: float
    min_time: float
    failure_count: int
    success_rate: float  # 0.0 – 1.0


def build_digest(results: List[BenchmarkResult]) -> List[DigestEntry]:
    """Aggregate all results by command into DigestEntry records."""
    from collections import defaultdict

    buckets: dict = defaultdict(list)
    failures: dict = defaultdict(int)
    totals: dict = defaultdict(int)

    for r in results:
        totals[r.command] += 1
        if r.exit_code == 0 and r.elapsed is not None:
            buckets[r.command].append(r.elapsed)
        else:
            failures[r.command] += 1

    entries: List[DigestEntry] = []
    for cmd, times in sorted(buckets.items()):
        n = len(times)
        total = totals[cmd]
        fail = failures.get(cmd, 0)
        entries.append(
            DigestEntry(
                command=cmd,
                sample_count=n,
                mean_time=mean(times),
                median_time=median(times),
                stdev_time=stdev(times) if n > 1 else 0.0,
                min_time=bm_min(times),
                failure_count=fail,
                success_rate=n / total if total else 0.0,
            )
        )
    return entries


def render_digest_table(entries: List[DigestEntry]) -> str:
    """Render digest entries as a plain-text table."""
    if not entries:
        return "No digest data available."

    header = f"{'Command':<30} {'N':>4} {'Mean':>9} {'Median':>9} {'Stdev':>9} {'Min':>9} {'Fail':>5} {'OK%':>6}"
    sep = "-" * len(header)
    rows = [header, sep]
    for e in entries:
        rows.append(
            f"{e.command:<30} {e.sample_count:>4} "
            f"{e.mean_time:>9.4f} {e.median_time:>9.4f} "
            f"{e.stdev_time:>9.4f} {e.min_time:>9.4f} "
            f"{e.failure_count:>5} {e.success_rate * 100:>5.1f}%"
        )
    return "\n".join(rows)
