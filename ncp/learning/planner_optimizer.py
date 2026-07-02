"""Planner optimizer — learns which plan shapes succeed."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ncp.learning.experience_db import ExperienceDB


@dataclass
class PlannerOptimizer:
    experience: ExperienceDB
    _by_size: dict[int, list[float]] = field(default_factory=lambda: defaultdict(list))

    def record_plan(self, node_count: int, success_rate: float) -> None:
        self._by_size[node_count].append(success_rate)

    def preferred_plan_size(self, default: int = 2) -> int:
        best_size, best_rate = default, -1.0
        for size, rates in self._by_size.items():
            avg = sum(rates) / len(rates)
            if avg > best_rate:
                best_size, best_rate = size, avg
        return best_size

    def stats(self) -> dict[int, float]:
        return {size: sum(rates) / len(rates) for size, rates in self._by_size.items()}
