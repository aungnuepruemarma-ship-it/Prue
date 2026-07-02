"""Lifecycle management - startup and shutdown sequences.

Startup:
    Load Config -> Init Logger -> Load Plugins -> Create Container
    -> Create Runtime -> Register Events -> Init Storage -> Init Memory
    -> Init Planner -> Init Router -> Start Scheduler -> Ready

Shutdown:
    Stop Scheduler -> Flush Events -> Save Memory -> Save Graph
    -> Save Storage -> Close Adapters -> Exit
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from ncp.events.bus import EventBus
from ncp.events.event import Event, EventType
from ncp.runtime.state import RuntimeState, RuntimeStatus
from ncp.utils.logger import get_logger
from ncp.utils.timeutils import utcnow

logger = get_logger(__name__)


@dataclass
class LifecycleManager:
    """Manages system startup and shutdown."""
    event_bus: EventBus
    state: RuntimeState = field(default_factory=RuntimeState)

    def startup(self) -> None:
        """Execute startup sequence."""
        logger.info("=== NCP Startup ===")
        self.state.status = RuntimeStatus.STARTING

        # 1. Start event bus
        self.event_bus.start()
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_STARTED.value,
            payload={"status": "starting"},
        ))

        logger.info("Startup complete")
        self.state.status = RuntimeStatus.RUNNING
        self.state.start_time = utcnow()

    def shutdown(self) -> None:
        """Execute graceful shutdown."""
        logger.info("=== NCP Shutdown ===")
        self.state.status = RuntimeStatus.SHUTTING_DOWN

        # 1. Flush remaining events
        self.event_bus.flush()

        # 2. Emit shutdown event
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_SHUTDOWN.value,
            payload={"status": "shutting_down"},
        ))

        # 3. Stop event bus
        self.event_bus.stop()

        logger.info("Shutdown complete")
        self.state.status = RuntimeStatus.STOPPED

    def snapshot(self) -> Dict[str, Any]:
        """Create state snapshot."""
        return self.state.to_dict()
