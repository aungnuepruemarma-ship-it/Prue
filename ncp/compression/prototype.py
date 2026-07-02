"""Prototype-based compression."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Prototype:
    """A representative exemplar for repeated structures."""
    id: UUID = field(default_factory=uuid4)
    pattern: str = ""
    occurrences: int = 0
    instances: List[str] = field(default_factory=list)


class PrototypeCompressor:
    """Compresses by finding and reusing prototypes."""

    def __init__(self):
        self.prototypes: Dict[str, Prototype] = {}

    def find_prototype(self, data: str) -> Optional[Prototype]:
        """Find matching prototype."""
        for proto in self.prototypes.values():
            if proto.pattern in data:
                return proto
        return None

    def add_prototype(self, pattern: str) -> Prototype:
        """Add a new prototype."""
        proto = Prototype(pattern=pattern, occurrences=1)
        self.prototypes[str(proto.id)] = proto
        return proto
