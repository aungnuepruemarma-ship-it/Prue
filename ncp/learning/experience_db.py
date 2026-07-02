"""Experience database — every execution outcome, queryable for learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ncp.storage.relational_store import RelationalStore
from ncp.utils.timeutils import utcnow

TABLE = "experience"


@dataclass
class ExperienceDB:
    store: RelationalStore

    def record(self, *, run_id: str, goal: str, task_type: str, provider_id: str,
               success: bool, reward: float, duration_ms: float = 0.0,
               confidence: float = 0.0, metadata: dict[str, Any] | None = None) -> None:
        self.store.insert(TABLE, {
            "run_id": run_id,
            "goal": goal,
            "task_type": task_type,
            "provider_id": provider_id,
            "success": int(success),
            "reward": reward,
            "duration_ms": duration_ms,
            "confidence": confidence,
            "metadata": metadata or {},
            "recorded_at": utcnow().isoformat(),
        })

    def episodes(self, where: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.store.query(TABLE, where)

    def provider_stats(self) -> dict[tuple[str, str], dict[str, float]]:
        """Aggregate success/reward per (provider, task_type)."""
        stats: dict[tuple[str, str], dict[str, float]] = {}
        for episode in self.episodes():
            key = (episode["provider_id"], episode["task_type"])
            bucket = stats.setdefault(key, {"count": 0.0, "successes": 0.0, "reward": 0.0})
            bucket["count"] += 1
            bucket["successes"] += episode["success"]
            bucket["reward"] += episode["reward"]
        for bucket in stats.values():
            bucket["success_rate"] = bucket["successes"] / bucket["count"]
            bucket["avg_reward"] = bucket["reward"] / bucket["count"]
        return stats

    @property
    def count(self) -> int:
        return self.store.count(TABLE)
