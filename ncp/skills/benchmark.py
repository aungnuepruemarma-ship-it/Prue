"""Skill benchmark - Score skill quality."""

from dataclasses import dataclass
from typing import Dict

from ncp.core.entities import Skill


@dataclass
class SkillBenchmark:
    """Measures skill quality: speed, reliability, reuse, cost."""

    def benchmark(self, skill: Skill) -> Dict[str, float]:
        """Run benchmarks on a skill."""
        return {
            "success_rate": skill.success_rate,
            "avg_execution_time": skill.average_execution_time_ms,
            "confidence": skill.confidence,
            "reuse_score": min(1.0, skill.success_count / 100),
        }

    def score(self, skill: Skill) -> float:
        """Compute overall skill score."""
        metrics = self.benchmark(skill)
        return (
            metrics["success_rate"] * 0.4 +
            (1.0 / (1.0 + metrics["avg_execution_time"] / 1000)) * 0.2 +
            metrics["confidence"] * 0.2 +
            metrics["reuse_score"] * 0.2
        )
