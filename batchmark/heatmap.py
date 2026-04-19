from dataclasses import dataclass
from typing import List, Dict, Tuple
from batchmark.runner import BenchmarkResult

_BLOCKS = " ░▒▓█"


@dataclass
class HeatmapCell:
    command: str
    size: int
    mean_time: float
    intensity: float  # 0.0 to 1.0


def build_heatmap(
    results: List[BenchmarkResult],
) -> Tuple[List[str], List[int], List[List[HeatmapCell]]]:
    """Return (commands, sizes, grid) where grid[cmd_idx][size_idx] = HeatmapCell."""
    from batchmark.runner import mean

    ok = [r for r in results if r.success]
    if not ok:
        return [], [], []

    commands = sorted({r.command for r in ok})
    sizes = sorted({r.size for r in ok})

    lookup: Dict[Tuple[str, int], float] = {}
    for r in ok:
        key = (r.command, r.size)
        times = lookup.setdefault(key, [])
        if isinstance(times, list):
            times.append(r.mean_time)

    averaged: Dict[Tuple[str, int], float] = {
        k: sum(v) / len(v) for k, v in lookup.items() if isinstance(v, list)
    }

    all_times = list(averaged.values())
    lo, hi = min(all_times), max(all_times)
    span = hi - lo if hi != lo else 1.0

    grid = []
    for cmd in commands:
        row = []
        for sz in sizes:
            t = averaged.get((cmd, sz))
            if t is None:
                row.append(HeatmapCell(cmd, sz, float("nan"), 0.0))
            else:
                intensity = (t - lo) / span
                row.append(HeatmapCell(cmd, sz, t, intensity))
        grid.append(row)

    return commands, sizes, grid


def _block(intensity: float) -> str:
    if intensity != intensity:  # nan
        return "?"
    idx = min(int(intensity * (len(_BLOCKS) - 1)), len(_BLOCKS) - 1)
    return _BLOCKS[idx]


def render_heatmap_table(results: List[BenchmarkResult]) -> str:
    commands, sizes, grid = build_heatmap(results)
    if not commands:
        return "No data."

    size_labels = [str(s) for s in sizes]
    col_w = max(max(len(s) for s in size_labels), 3)
    cmd_w = max(len(c) for c in commands)

    header = " " * cmd_w + "  " + "  ".join(s.rjust(col_w) for s in size_labels)
    sep = "-" * len(header)
    lines = [header, sep]

    for cmd, row in zip(commands, grid):
        cells = []
        for cell in row:
            symbol = _block(cell.intensity)
            cells.append(symbol.rjust(col_w))
        lines.append(cmd.ljust(cmd_w) + "  " + "  ".join(cells))

    return "\n".join(lines)
