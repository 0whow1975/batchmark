"""Detect plateau regions where performance stabilizes across input sizes."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult, mean


@dataclass
class PlateauRegion:
    command: str
    start_size: int
    end_size: int
    avg_time: float
    variance_pct: float  # max deviation from mean as % of mean
    is_plateau: bool


def detect_plateaus(
    results: List[BenchmarkResult],
    threshold_pct: float = 10.0,
    min_points: int = 3,
) -> List[PlateauRegion]:
    """Group results by command and detect plateau regions.

    A plateau is a contiguous run of >= min_points sizes where the mean time
    deviates by no more than threshold_pct percent from the window mean.
    """
    from batchmark.filter import group_by_command

    regions: List[PlateauRegion] = []
    grouped = group_by_command([r for r in results if r.success])

    for command, cmd_results in grouped.items():
        sorted_results = sorted(cmd_results, key=lambda r: r.size)
        n = len(sorted_results)
        if n < min_points:
            continue

        i = 0
        while i <= n - min_points:
            window = sorted_results[i : i + min_points]
            times = [mean(r.times) for r in window]
            window_mean = mean(times)
            if window_mean == 0:
                i += 1
                continue
            max_dev = max(abs(t - window_mean) / window_mean * 100 for t in times)

            if max_dev <= threshold_pct:
                # Extend window as far as plateau holds
                j = i + min_points
                while j < n:
                    candidate_times = [mean(sorted_results[k].times) for k in range(i, j + 1)]
                    ext_mean = mean(candidate_times)
                    if ext_mean == 0:
                        break
                    ext_dev = max(abs(t - ext_mean) / ext_mean * 100 for t in candidate_times)
                    if ext_dev <= threshold_pct:
                        j += 1
                    else:
                        break
                plateau_results = sorted_results[i:j]
                all_times = [mean(r.times) for r in plateau_results]
                plateau_mean = mean(all_times)
                variance = max(abs(t - plateau_mean) / plateau_mean * 100 for t in all_times)
                regions.append(
                    PlateauRegion(
                        command=command,
                        start_size=plateau_results[0].size,
                        end_size=plateau_results[-1].size,
                        avg_time=plateau_mean,
                        variance_pct=round(variance, 2),
                        is_plateau=True,
                    )
                )
                i = j
            else:
                i += 1

    return regions


def render_plateau_table(regions: List[PlateauRegion]) -> str:
    if not regions:
        return "No plateau regions detected."
    header = f"{'Command':<30} {'Start':>10} {'End':>10} {'Avg(s)':>10} {'Var%':>8}"
    sep = "-" * len(header)
    rows = [header, sep]
    for r in regions:
        rows.append(
            f"{r.command:<30} {r.start_size:>10} {r.end_size:>10} "
            f"{r.avg_time:>10.4f} {r.variance_pct:>8.2f}"
        )
    return "\n".join(rows)
