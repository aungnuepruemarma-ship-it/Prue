"""Constraint policies."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConstraintPolicies:
    """System-wide constraint policies."""

    max_execution_time_ms: float = 300000  # 5 minutes
    max_cost_per_task: float = 1.0
    max_retries: int = 3
    allowed_capabilities: List[str] = field(default_factory=list)
    blocked_capabilities: List[str] = field(default_factory=list)

    def is_capability_allowed(self, name: str) -> bool:
        if self.blocked_capabilities and name in self.blocked_capabilities:
            return False
        if self.allowed_capabilities and name not in self.allowed_capabilities:
            return False
        return True
