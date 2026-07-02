"""Cache store - Hot cache for recent items."""

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, Optional


@dataclass
class CacheStore:
    """In-memory cache with TTL."""

    _cache: Dict[str, Any] = field(default_factory=dict)
    _expires: Dict[str, float] = field(default_factory=dict)
    default_ttl: float = 300.0  # 5 minutes

    def get(self, key: str) -> Optional[Any]:
        """Get cached item if not expired."""
        if key in self._cache:
            if time() < self._expires.get(key, 0):
                return self._cache[key]
            else:
                self.invalidate(key)
        return None

    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """Cache an item."""
        self._cache[key] = value
        self._expires[key] = time() + (ttl or self.default_ttl)

    def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        self._cache.pop(key, None)
        self._expires.pop(key, None)

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._expires.clear()
