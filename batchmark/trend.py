from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BenchmarkResult


@dataclass
class TrendPoint:
    tag: str
    size: int
    mean: float
    median: float


@dataclass
class TrendSeries:
    command: str
    points: List[TrendPoint]

    @property
    def improving(self) -> Optional[bool]:
        means = [p.mean for p in self.points]
        if len(means) < 2:
            return None
        return means[-1] < means[0]


def build_trend(results_by_tag: dict) -> List[TrendSeries]:
    """results_by_tag: {tag: [BenchmarkResult]}"""
    series_map = {}
    for tag, results in results_by_tag.items():
        for r in results:
            if not r.success:
                continue
            key = (r.command, r.size)
            if key not in series_map:
                series_map[key] = []
            series_map[key].append((tag, r))

    series_list = []
    seen_commands = {}
    for (command, size), entries in sorted(series_map.items()):
        points = [
            TrendPoint(tag=tag, size=size, mean=r.mean, median=r.median)
            for tag, r in entries
        ]
        if command not in seen_commands:
            seen_commands[command] = TrendSeries(command=command, points=[])
            series_list.append(seen_commands[command])
        seen_commands[command].points.extend(points)

    return series_list


def render_trend_table(series_list: List[TrendSeries]) -> str:
    if not series_list:
        return "No trend data available."

    header = f"{'Command':<30} {'Tag':<15} {'Size':>8} {'Mean':>10} {'Median':>10}"
    sep = "-" * len(header)
    rows = [header, sep]

    for series in series_list:
        for pt in series.points:
            rows.append(
                f"{series.command:<30} {pt.tag:<15} {pt.size:>8} "
                f"{pt.mean:>10.4f} {pt.median:>10.4f}"
            )
        rows.append("")

    return "\n".join(rows).rstrip()
