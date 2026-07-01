from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class HistoryLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event: dict[str, Any]) -> None:
        self.events.append(dict(event))

    def ngrams(self, n: int = 2) -> list[tuple[str, ...]]:
        ops = [e.get("candidate") or e.get("op") for e in self.events]
        ops = [op for op in ops if op]
        out = []
        for i in range(max(0, len(ops) - n + 1)):
            out.append(tuple(ops[i:i+n]))
        return out
