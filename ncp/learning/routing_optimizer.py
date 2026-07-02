"""Routing optimizer — historical success becomes the routing policy.

Instead of ``if code: use X``, the selector consults a policy learned from
the experience database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.capabilities.registry import ProviderRecord
from ncp.capabilities.selector import default_score
from ncp.learning.experience_db import ExperienceDB


@dataclass
class RoutingOptimizer:
    experience: ExperienceDB
    min_episodes: int = 3
    _stats: dict[tuple[str, str], dict[str, float]] = field(default_factory=dict)

    def refresh(self) -> None:
        self._stats = self.experience.provider_stats()

    def learned_policy(self, record: ProviderRecord, requirements: dict[str, Any]) -> float:
        """ScoreFn for ProviderSelector: observed outcomes dominate priors."""
        base = default_score(record, requirements)
        key = (record.id, requirements.get("task_type", ""))
        stats = self._stats.get(key)
        if stats and stats["count"] >= self.min_episodes:
            return base + 3.0 * stats["success_rate"] + stats["avg_reward"]
        # fall back to aggregate provider performance across task types
        totals = [s for (pid, _), s in self._stats.items() if pid == record.id]
        if totals:
            count = sum(s["count"] for s in totals)
            if count >= self.min_episodes:
                success = sum(s["successes"] for s in totals) / count
                return base + 2.0 * success
        return base

    def best_provider(self, task_type: str) -> str | None:
        candidates = [
            (stats["success_rate"], stats["avg_reward"], pid)
            for (pid, tt), stats in self._stats.items()
            if tt == task_type and stats["count"] >= self.min_episodes
        ]
        if not candidates:
            return None
        return max(candidates)[2]
