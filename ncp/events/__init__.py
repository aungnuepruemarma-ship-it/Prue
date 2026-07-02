"""NCP Events - Event-driven communication system.

Production paths publish through :class:`EventPublisher` (typed, sourced,
prioritized) and route background workers through :class:`EventDispatcher`.
:class:`EventSubscriber` is an intentionally thin alternate subscribe API —
behaviorally identical to ``EventBus.subscribe``/``subscribe_all`` — kept
for callers that want an object handle instead of the bus itself; it is
unit-tested directly rather than force-wired into the kernel.
"""

from ncp.events.bus import EventBus
from ncp.events.dispatcher import EventDispatcher
from ncp.events.event import Event, EventType
from ncp.events.priority import EventPriority
from ncp.events.publisher import EventPublisher
from ncp.events.queue import EventQueue
from ncp.events.registry import EventRegistry
from ncp.events.subscriber import EventSubscriber

__all__ = [
    "Event", "EventType", "EventBus", "EventDispatcher",
    "EventPriority", "EventRegistry", "EventPublisher",
    "EventSubscriber", "EventQueue",
]
