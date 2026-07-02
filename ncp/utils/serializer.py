"""Serialization utilities."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict


class Serializer:
    """JSON serializer for NCP entities."""

    @staticmethod
    def to_json(obj: Any) -> str:
        """Serialize to JSON string."""
        return json.dumps(Serializer.to_dict(obj), indent=2, default=str)

    @staticmethod
    def from_json(data: str) -> Any:
        """Deserialize from JSON string."""
        return json.loads(data)

    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary."""
        from ncp.core.entities import Entity  # deferred: utils must not depend on core at import time
        if isinstance(obj, Entity):
            return obj.to_dict()
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, (list, tuple)):
            return [Serializer.to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {k: Serializer.to_dict(v) for k, v in obj.items()}
        return obj
