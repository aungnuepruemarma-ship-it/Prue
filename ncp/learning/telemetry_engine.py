"""Telemetry engine — subscribes to the event bus and records everything."""

from __future__ import annotations

from dataclasses import dataclass, field

from ncp.events.bus import EventBus
from ncp.events.event import Event
from ncp.storage.relational_store import RelationalStore
from ncp.utils.timeutils import utcnow

TABLE = "telemetry"


@dataclass
class TelemetryEngine:
    store: RelationalStore
    counters: dict[str, int] = field(default_factory=dict)

    def attach(self, bus: EventBus) -> None:
        bus.subscribe_all(self.on_event)

    def on_event(self, event: Event) -> None:
        self.counters[event.type] = self.counters.get(event.type, 0) + 1
        self.store.insert(TABLE, {
            "event_type": event.type,
            "source": event.source or "",
            "payload": event.payload,
            "recorded_at": utcnow().isoformat(),
        })

    def events_of_type(self, event_type: str) -> list[dict]:
        return self.store.query(TABLE, {"event_type": event_type})

    @property
    def total_events(self) -> int:
        return self.store.count(TABLE)
