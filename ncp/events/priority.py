"""Event priority levels."""

from enum import IntEnum


class EventPriority(IntEnum):
    """Priority levels for event processing."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4
