"""Envelope analysis: track min/max bounds across runs to detect performance spread."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple

from batchmark.runner import BenchmarkResult


@dataclass
class EnvelopeResult:
    command: str
    size: int
    lo: float   # minimum observed mean time
    hi: float   # maximum observed mean time
    spread: float  # hi - lo
    spread_pct: float  # spread / lo * 100


def build_envelope(
    results: List[BenchmarkResult],
    command_filter: str | None = None,
) -> Dict[Tuple[str, int], EnvelopeResult]:
    """Group results by (command, size) and compute lo/hi envelope."""
    buckets: Dict[Tuple[str, int], List[float]] = {}

    for r in results:
        if not r.success:
            continue
        if command_filter and r.command != command_filter:
            continue
        key = (r.command, r.size)
        buckets.setdefault(key, []).append(r.mean)

    envelope: Dict[Tuple[str, int], EnvelopeResult] = {}
    for (cmd, size), times in buckets.items():
        lo = min(times)
        hi = max(times)
        spread = hi - lo
        spread_pct = (spread / lo * 100) if lo > 0 else 0.0
        envelope[(cmd, size)] = EnvelopeResult(
            command=cmd,
            size=size,
            lo=lo,
            hi=hi,
            spread=spread,
            spread_pct=spread_pct,
        )

    return envelope


def render_envelope_table(envelope: Dict[Tuple[str, int], EnvelopeResult]) -> str:
    """Render envelope results as a plain-text table."""
    if not envelope:
        return "No envelope data."

    header = f"{'Command':<30} {'Size':>8} {'Lo (s)':>10} {'Hi (s)':>10} {'Spread (s)':>12} {'Spread %':>10}"
    sep = "-" * len(header)
    rows = [header, sep]

    for (cmd, size), e in sorted(envelope.items()):
        rows.append(
            f"{cmd:<30} {size:>8} {e.lo:>10.4f} {e.hi:>10.4f} {e.spread:>12.4f} {e.spread_pct:>9.1f}%"
        )

    return "\n".join(rows)
