"""Annotate benchmark results with custom labels and notes."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class AnnotatedResult:
    result: BenchmarkResult
    label: Optional[str] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)


def annotate_results(
    results: List[BenchmarkResult],
    label: Optional[str] = None,
    notes: str = "",
    tags: Optional[List[str]] = None,
) -> List[AnnotatedResult]:
    """Wrap results with annotation metadata."""
    return [
        AnnotatedResult(
            result=r,
            label=label,
            notes=notes,
            tags=list(tags) if tags else [],
        )
        for r in results
    ]


def group_by_label(
    annotated: List[AnnotatedResult],
) -> Dict[Optional[str], List[AnnotatedResult]]:
    """Group annotated results by their label."""
    groups: Dict[Optional[str], List[AnnotatedResult]] = {}
    for ar in annotated:
        groups.setdefault(ar.label, []).append(ar)
    return groups


def render_annotated_table(annotated: List[AnnotatedResult]) -> str:
    """Render annotated results as a plain-text table."""
    if not annotated:
        return "No annotated results."

    header = f"{'Label':<20} {'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Tags'}"
    sep = "-" * len(header)
    rows = [header, sep]

    for ar in annotated:
        r = ar.result
        mean_s = f"{r.mean:.4f}" if r.mean is not None else "N/A"
        label = ar.label or ""
        tags = ",".join(ar.tags)
        rows.append(f"{label:<20} {r.command:<30} {r.size:>8} {mean_s:>10} {tags}")

    return "\n".join(rows)
