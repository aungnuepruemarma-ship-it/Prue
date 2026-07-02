"""Storage manager — the unified facade over every persistence backend.

Owns the on-disk layout from the Phase-6 spec:

    storage/
    ├── relational/    structured rows (sqlite3; postgres slot)
    ├── vectors/       embeddings
    ├── graph/         knowledge graphs
    ├── artifacts/     reports, code, images
    ├── checkpoints/   execution state
    ├── world_state/   active session/projects
    ├── telemetry/     learning telemetry (experience db)
    ├── backups/       zip snapshots
    ├── cache/         temporary values
    └── registry/      provider registry persistence

Backends are pluggable via ``register_backend``; the defaults are stdlib.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from ncp.storage.artifact_store import ArtifactStore
from ncp.storage.backup_manager import BackupManager
from ncp.storage.cache import CacheStore
from ncp.storage.checkpoint_store import CheckpointStore
from ncp.storage.graph_store import GraphStore
from ncp.storage.object_store import ObjectStore
from ncp.storage.relational_store import RelationalStore
from ncp.storage.snapshot import SnapshotStore
from ncp.storage.vector_store import VectorStore

SUBDIRS = (
    "relational", "vectors", "graph", "artifacts", "checkpoints",
    "world_state", "telemetry", "backups", "cache", "registry",
)


class StorageManager:
    """Single entry point to all persistence, per the AI-OS storage spec."""

    def __init__(self, root: str = "storage", backends: dict[str, Callable[..., Any]] | None = None):
        self.root = Path(root)
        for sub in SUBDIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        factories: dict[str, Callable[..., Any]] = {
            "relational": lambda: RelationalStore(str(self.root / "relational" / "ncp.db")),
            "vectors": VectorStore,
            "graph": GraphStore,
            "objects": ObjectStore,
            "cache": CacheStore,
            "snapshots": SnapshotStore,
            "artifacts": lambda: ArtifactStore(str(self.root / "artifacts")),
            "checkpoints": lambda: CheckpointStore(str(self.root / "checkpoints")),
            "backups": lambda: BackupManager(str(self.root), str(self.root / "backups")),
        }
        if backends:
            factories.update(backends)
        self.relational: RelationalStore = factories["relational"]()
        self.vectors: VectorStore = factories["vectors"]()
        self.graph: GraphStore = factories["graph"]()
        self.objects: ObjectStore = factories["objects"]()
        self.cache: CacheStore = factories["cache"]()
        self.snapshots: SnapshotStore = factories["snapshots"]()
        self.artifacts: ArtifactStore = factories["artifacts"]()
        self.checkpoints: CheckpointStore = factories["checkpoints"]()
        self.backups: BackupManager = factories["backups"]()

    # -- world state / registry documents ---------------------------------
    def save_document(self, area: str, name: str, data: dict[str, Any]) -> Path:
        path = self.root / area / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    def load_document(self, area: str, name: str) -> dict[str, Any] | None:
        path = self.root / area / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def stats(self) -> dict[str, int]:
        return {sub: sum(1 for p in (self.root / sub).rglob("*") if p.is_file()) for sub in SUBDIRS}
