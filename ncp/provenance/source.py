"""Source tracking - Origin of memory items."""

from dataclasses import dataclass, field
from datetime import datetime

from ncp.utils.timeutils import utcnow


@dataclass
class Source:
    """Origin of a memory item, result, or skill."""
    type: str = ""  # "user", "system", "llm", "tool", "file"
    identifier: str = ""  # User ID, model name, tool name
    timestamp: datetime = field(default_factory=utcnow)
    context: str = ""  # Additional context about the source
