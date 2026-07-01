from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Diagnostics:
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def summary(self) -> dict[str, int]:
        return dict(self.counters)
