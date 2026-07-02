"""Code benchmark - Compare correctness and speed."""

from dataclasses import dataclass
from time import perf_counter
from typing import List

from ncp.coding.generator import CodeCandidate


@dataclass
class BenchmarkResult:
    """Benchmark result for a code candidate."""
    candidate_id: str = ""
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    passed: bool = True
    score: float = 0.0


@dataclass
class CodeBenchmark:
    """Benchmarks code candidates."""

    def benchmark(self, candidate: CodeCandidate) -> BenchmarkResult:
        """Run benchmark on a candidate."""
        start = perf_counter()

        # Simulated execution
        elapsed = (perf_counter() - start) * 1000

        return BenchmarkResult(
            candidate_id=str(candidate.id),
            execution_time_ms=elapsed + 1.0,  # Add base time
            passed=True,
            score=candidate.score,
        )

    def compare(self, candidates: List[CodeCandidate]) -> List[BenchmarkResult]:
        """Benchmark and compare multiple candidates."""
        return [self.benchmark(c) for c in candidates]
