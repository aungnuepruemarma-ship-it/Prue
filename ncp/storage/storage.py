"""Storage - Unified persistence API.

Routes entities, graphs, embeddings, objects, events to the right store.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ncp.interfaces.storage import StorageInterface
from ncp.storage.cache import CacheStore
from ncp.storage.entity_store import EntityStore
from ncp.storage.snapshot import SnapshotStore
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Storage(StorageInterface):
    """Unified storage backend.

    Routes data to appropriate stores.
    """
    config: Config = None

    entity_store: EntityStore = field(default_factory=EntityStore)
    snapshot_store: SnapshotStore = field(default_factory=SnapshotStore)
    cache: CacheStore = field(default_factory=CacheStore)

    _data: Dict[str, Any] = field(default_factory=dict, repr=False)

    def save(self, key: str, data: Any) -> None:
        """Save data."""
        self._data[key] = data
        self.entity_store.store(key, data)
        logger.debug("Saved: %s", key)

    def load(self, key: str) -> Optional[Any]:
        """Load data."""
        # Check cache first
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        # Check memory store
        if key in self._data:
            self.cache.set(key, self._data[key])
            return self._data[key]

        return None

    def delete(self, key: str) -> None:
        """Delete data."""
        if key in self._data:
            del self._data[key]
        self.cache.invalidate(key)
        logger.debug("Deleted: %s", key)

    def list_keys(self, prefix: str = "") -> List[str]:
        """List keys with prefix."""
        return [k for k in self._data.keys() if k.startswith(prefix)]

    def snapshot(self, name: str) -> None:
        """Create snapshot."""
        self.snapshot_store.create(name, self._data)
        logger.info("Snapshot created: %s", name)
