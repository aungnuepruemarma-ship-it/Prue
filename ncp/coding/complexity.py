"""Complexity analyzer - Estimate time and space complexity."""

from dataclasses import dataclass


@dataclass
class ComplexityReport:
    """Complexity analysis results."""
    time_complexity: str = "O(1)"
    space_complexity: str = "O(1)"
    estimated_ops: int = 0
    estimated_memory_mb: float = 0.0
    score: float = 1.0


@dataclass
class ComplexityAnalyzer:
    """Estimates time and space complexity of code."""

    def analyze(self, code: str) -> ComplexityReport:
        """Analyze code complexity."""
        # Simple heuristic analysis
        lines = code.split("\n")
        loops = sum(1 for line in lines if any(kw in line for kw in ["for ", "while "]))

        if loops > 2:
            time_complexity = "O(n^2)"
        elif loops > 0:
            time_complexity = "O(n)"
        else:
            time_complexity = "O(1)"

        return ComplexityReport(
            time_complexity=time_complexity,
            space_complexity="O(n)" if loops > 0 else "O(1)",
            estimated_ops=len(lines) * max(1, loops),
        )
