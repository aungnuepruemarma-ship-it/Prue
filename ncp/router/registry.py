"""Capability registry - Stores capability cards."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ncp.interfaces.capability import CapabilityCard


@dataclass
class CapabilityRegistry:
    """Registers tools/models and stores capability cards."""

    capabilities: Dict[str, CapabilityCard] = field(default_factory=dict)

    def register(self, card: CapabilityCard) -> None:
        """Register a capability."""
        self.capabilities[card.name] = card

    def get(self, name: str) -> Optional[CapabilityCard]:
        """Get a capability by name."""
        return self.capabilities.get(name)

    def list_all(self) -> List[CapabilityCard]:
        """List all registered capabilities."""
        return list(self.capabilities.values())

    def find_by_type(self, cap_type: str) -> List[CapabilityCard]:
        """Find capabilities by type."""
        return [c for c in self.capabilities.values() if c.type == cap_type]

    def find_by_input_type(self, input_type: str) -> List[CapabilityCard]:
        """Find capabilities accepting input type."""
        return [c for c in self.capabilities.values()
                if input_type in c.input_types]

    @property
    def count(self) -> int:
        return len(self.capabilities)
