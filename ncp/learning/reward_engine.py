"""Reward engine — turns an execution outcome into a scalar learning signal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RewardEngine:
    success_reward: float = 1.0
    failure_penalty: float = -1.0
    confidence_weight: float = 0.5
    cost_weight: float = 0.1

    def compute(self, output: dict[str, Any], verification: dict[str, Any] | None = None) -> float:
        success = output.get("status") in {"success", "accepted"}
        reward = self.success_reward if success else self.failure_penalty
        verification = verification or {}
        reward += self.confidence_weight * float(verification.get("confidence", output.get("confidence", 0.0)))
        reward -= self.cost_weight * float(output.get("cost", 0.0))
        if verification and not verification.get("approved", True):
            reward -= 0.5
        return reward
