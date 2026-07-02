from __future__ import annotations

import uuid
from uuid import UUID


def new_id(prefix: str = "n") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def generate_id() -> UUID:
    """Generate a new unique identifier (platform-style UUID)."""
    return uuid.uuid4()

def id_from_string(value: str) -> UUID:
    """Create a UUID from its string form."""
    return uuid.UUID(value)
