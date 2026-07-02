"""Hashing utilities."""

import hashlib
import json
from typing import Any, Dict


def hash_dict(data: Dict[str, Any]) -> str:
    """Create deterministic hash of a dictionary."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def hash_string(data: str) -> str:
    """Create SHA-256 hash of a string."""
    return hashlib.sha256(data.encode()).hexdigest()
