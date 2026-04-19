import subprocess
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BenchmarkResult:
    command: str
    input_size: int
    runs: int
    times: List[float] = field(default_factory=list)
    exit_codes: List[int] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def mean(self) -> float:
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def median(self) -> float:
        return statistics.median(self.times) if self.times else 0.0

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def min(self) -> float:
        return min(self.times) if self.times else 0.0

    @property
    def max(self) -> float:
        return max(self.times) if self.times else 0.0

    @property
    def success_rate(self) -> float:
        if not self.exit_codes:
            return 0.0
        return sum(1 for c in self.exit_codes if c == 0) / len(self.exit_codes)


def run_benchmark(
    command: str,
    input_size: int,
    runs: int = 5,
    timeout: float = 30.0,
    stdin_data: Optional[bytes] = None,
) -> BenchmarkResult:
    result = BenchmarkResult(command=command, input_size=input_size, runs=runs)

    for _ in range(runs):
        try:
            start = time.perf_counter()
            proc = subprocess.run(
                command,
                shell=True,
                input=stdin_data,
                capture_output=True,
                timeout=timeout,
            )
            elapsed = time.perf_counter() - start
            result.times.append(elapsed)
            result.exit_codes.append(proc.returncode)
        except subprocess.TimeoutExpired:
            result.error = f"Command timed out after {timeout}s"
            break
        except Exception as e:
            result.error = str(e)
            break

    return result
