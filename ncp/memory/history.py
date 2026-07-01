from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def ngrams_from_events(events: list[dict[str, Any]], n: int = 2) -> list[tuple[str, ...]]:
    ops = [e.get("candidate") or e.get("op") for e in events]
    ops = [op for op in ops if op]
    return [tuple(ops[i:i + n]) for i in range(max(0, len(ops) - n + 1))]

@dataclass
class HistoryLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event: dict[str, Any]) -> None:
        self.events.append(dict(event))

    def ngrams(self, n: int = 2) -> list[tuple[str, ...]]:
        return ngrams_from_events(self.events, n)
