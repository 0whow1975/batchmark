"""Budget enforcement: flag results that exceed a time budget per input size."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class BudgetResult:
    result: BenchmarkResult
    budget: float
    exceeded: bool
    delta: float  # actual - budget (negative means under budget)


def check_budget(
    results: List[BenchmarkResult],
    budget: float,
    command: Optional[str] = None,
) -> List[BudgetResult]:
    """Check each result against a time budget (in seconds).

    Args:
        results: List of benchmark results to evaluate.
        budget: Maximum allowed mean time in seconds.
        command: If provided, only check results for this command.

    Returns:
        List of BudgetResult for non-failed results matching the filter.
    """
    out: List[BudgetResult] = []
    for r in results:
        if r.failed:
            continue
        if command is not None and r.command != command:
            continue
        delta = r.mean - budget
        out.append(BudgetResult(
            result=r,
            budget=budget,
            exceeded=delta > 0,
            delta=delta,
        ))
    return out


def render_budget_table(budget_results: List[BudgetResult]) -> str:
    """Render a plain-text table of budget check results."""
    if not budget_results:
        return "No results to display."

    header = f"{'Command':<30} {'Size':>8} {'Mean(s)':>10} {'Budget(s)':>10} {'Delta(s)':>10} {'Status':>8}"
    sep = "-" * len(header)
    rows = [header, sep]

    for br in budget_results:
        r = br.result
        status = "OVER" if br.exceeded else "OK"
        rows.append(
            f"{r.command:<30} {r.size:>8} {r.mean:>10.4f} {br.budget:>10.4f} {br.delta:>+10.4f} {status:>8}"
        )

    over = sum(1 for br in budget_results if br.exceeded)
    rows.append(sep)
    rows.append(f"{over}/{len(budget_results)} results exceeded budget of {budget_results[0].budget:.4f}s")
    return "\n".join(rows)
