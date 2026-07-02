"""Capability Interface - Capability definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CapabilityCard:
    """Describes a capability available to the router."""
    name: str
    type: str  # "llm", "tool", "solver", "skill"
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    cost_per_call: float = 0.0
    reliability: float = 1.0
    safety_profile: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityInterface(ABC):
    """Abstract interface for capability providers."""

    @abstractmethod
    def get_card(self) -> CapabilityCard:
        """Get capability card.

        Returns:
            Capability description
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if capability is available.

        Returns:
            True if available
        """
        ...
