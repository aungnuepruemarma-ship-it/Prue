"""Router - Selects best model/tool/solver for each task.

Main routing logic with capability registry, history tracking, and policy-based selection.
"""

from dataclasses import dataclass, field
from typing import List

from ncp.core.entities import Task
from ncp.events.bus import EventBus
from ncp.events.event import EventType
from ncp.interfaces.capability import CapabilityCard
from ncp.interfaces.memory import MemoryInterface
from ncp.interfaces.router import RouterInterface
from ncp.router.history import RoutingHistory
from ncp.router.policy import RoutingPolicy
from ncp.router.registry import CapabilityRegistry
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Router(RouterInterface):
    """Main router implementation.

    Responsibilities:
    - Choose model/tool/solver for each task
    - Compare capability cards
    - Use history
    - Emit routing events
    """

    memory: MemoryInterface
    event_bus: EventBus
    config: Config

    registry: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    history: RoutingHistory = field(default_factory=RoutingHistory)
    policy: RoutingPolicy = None

    def __post_init__(self):
        if self.policy is None:
            self.policy = RoutingPolicy()
        self._setup_default_capabilities()

    def _setup_default_capabilities(self) -> None:
        """Register default capabilities."""
        defaults = [
            CapabilityCard(
                name="default_llm",
                type="llm",
                input_types=["text"],
                output_types=["text"],
                latency_ms=500.0,
                cost_per_call=0.01,
                reliability=0.9,
            ),
            CapabilityCard(
                name="fast_llm",
                type="llm",
                input_types=["text"],
                output_types=["text"],
                latency_ms=200.0,
                cost_per_call=0.005,
                reliability=0.8,
            ),
            CapabilityCard(
                name="tool_executor",
                type="tool",
                input_types=["command"],
                output_types=["result"],
                latency_ms=100.0,
                cost_per_call=0.001,
                reliability=0.95,
            ),
        ]
        for cap in defaults:
            self.registry.register(cap)

    def route(self, task: Task) -> CapabilityCard:
        """Select best capability for a task."""
        logger.debug("Routing task: %s", task.name)

        # Find matching capabilities
        candidates = self._find_candidates(task)

        if not candidates:
            # Fallback to default
            candidates = self.registry.list_all()

        # Build history context
        history_context = {}
        for cap in candidates:
            history_context[cap.name] = {
                "success_rate": self.history.get_success_rate(cap.name),
                "avg_latency": self.history.get_average_latency(cap.name),
            }

        # Select best
        selected = self.policy.select(task, candidates, history_context)

        # Emit event
        self.event_bus.publish(
            type=EventType.ROUTER_SELECTED.value,
            payload={
                "task": task.name,
                "capability": selected.name,
                "candidates": len(candidates),
            },
        )

        logger.info("Routed '%s' -> '%s'", task.name, selected.name)
        return selected

    def register(self, capability: CapabilityCard) -> None:
        """Register a new capability."""
        self.registry.register(capability)
        logger.info("Registered capability: %s", capability.name)

    def list_capabilities(self) -> List[CapabilityCard]:
        """List all available capabilities."""
        return self.registry.list_all()

    def _find_candidates(self, task: Task) -> List[CapabilityCard]:
        """Find candidate capabilities for a task."""
        # Match by capability_required field
        if task.capability_required:
            cap = self.registry.get(task.capability_required)
            if cap:
                return [cap]

        # Match by input types
        return self.registry.find_by_type("llm")  # Default to LLM
