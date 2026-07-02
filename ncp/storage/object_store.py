"""Object store - Files, documents, artifacts."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ObjectStore:
    """Stores objects and artifacts."""

    objects: Dict[str, bytes] = field(default_factory=dict)

    def store(self, key: str, data: bytes) -> None:
        self.objects[key] = data

    def retrieve(self, key: str) -> Optional[bytes]:
        return self.objects.get(key)
