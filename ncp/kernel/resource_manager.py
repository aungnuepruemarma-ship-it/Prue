"""Resource manager — bounded execution slots and budget accounting."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class ResourceManager:
    max_concurrent_tasks: int = 4
    budgets: dict[str, float] = field(default_factory=dict)
    spent: dict[str, float] = field(default_factory=dict)
    _active: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def acquire(self) -> bool:
        with self._lock:
            if self._active >= self.max_concurrent_tasks:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)

    def charge(self, budget: str, amount: float) -> bool:
        """Record spend; returns False when the budget is exhausted."""
        with self._lock:
            self.spent[budget] = self.spent.get(budget, 0.0) + amount
            limit = self.budgets.get(budget)
            return limit is None or self.spent[budget] <= limit

    def remaining(self, budget: str) -> float | None:
        limit = self.budgets.get(budget)
        if limit is None:
            return None
        return limit - self.spent.get(budget, 0.0)

    @property
    def active_tasks(self) -> int:
        return self._active
