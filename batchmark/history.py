"""Persist and load benchmark results to/from a JSON history file."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from batchmark.runner import BenchmarkResult

HISTORY_FILE = ".batchmark_history.json"


def _result_to_record(result: BenchmarkResult, tag: Optional[str] = None) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": tag,
        "command": result.command,
        "size": result.size,
        "exit_code": result.exit_code,
        "times": result.times,
        "mean": result.mean,
        "median": result.median,
        "stdev": result.stdev,
        "min": result.min,
        "max": result.max,
    }


def _record_to_result(record: dict) -> BenchmarkResult:
    return BenchmarkResult(
        command=record["command"],
        size=record["size"],
        exit_code=record["exit_code"],
        times=record["times"],
    )


def save_results(
    results: List[BenchmarkResult],
    path: str = HISTORY_FILE,
    tag: Optional[str] = None,
) -> None:
    """Append a run's results to the history file."""
    records = []
    if os.path.exists(path):
        with open(path, "r") as f:
            records = json.load(f)
    for r in results:
        records.append(_result_to_record(r, tag=tag))
    with open(path, "w") as f:
        json.dump(records, f, indent=2)


def load_results(
    path: str = HISTORY_FILE,
    tag: Optional[str] = None,
) -> List[BenchmarkResult]:
    """Load results from history file, optionally filtered by tag."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        records = json.load(f)
    if tag is not None:
        records = [r for r in records if r.get("tag") == tag]
    return [_record_to_result(r) for r in records]


def list_tags(path: str = HISTORY_FILE) -> List[str]:
    """Return sorted unique tags present in the history file."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        records = json.load(f)
    return sorted({r["tag"] for r in records if r.get("tag")})
