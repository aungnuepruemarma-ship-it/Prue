"""Version tracking for knowledge items."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class VersionedItem:
    """A versioned knowledge item."""
    id: UUID = field(default_factory=uuid4)
    version: int = 1
    previous_version: Optional[UUID] = None
    content_hash: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    change_summary: str = ""
