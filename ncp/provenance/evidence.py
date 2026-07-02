"""Evidence - Factual support for memory items."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Evidence:
    """Factual support including citations, links, checksums, observations."""
    type: str = ""  # "observation", "citation", "calculation", "reference"
    data: str = ""
    citations: List[str] = field(default_factory=list)
    checksum: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
