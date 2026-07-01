from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

Handler = Callable[..., Any]

@dataclass
class ExternalAdapter:
    """Registry of handlers for capabilities that live outside the process.

    Reasoner adapters route their transport (HTTP calls, subprocesses)
    through one of these, so tests and offline runs can inject fakes and
    availability can be introspected instead of hardcoded.
    """

    name: str
    handlers: dict[str, Handler] = field(default_factory=dict)

    def register(self, capability: str, handler: Handler) -> None:
        self.handlers[capability] = handler

    def available(self, capability: str | None = None) -> bool:
        if capability is None:
            return bool(self.handlers)
        return capability in self.handlers

    def call(self, capability: str, /, **kwargs: Any) -> Any:
        if capability not in self.handlers:
            raise KeyError(f"no handler registered for capability: {capability}")
        return self.handlers[capability](**kwargs)
