"""Archive memory - Cold storage for old snapshots."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from ncp.core.entities import Memory


@dataclass
class ArchiveEntry:
    """An entry in the archive."""
    id: UUID = field(default_factory=uuid4)
    content: str = ""
    compressed: bool = False
    original_size: int = 0
    compressed_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveMemory:
    """Cold storage for old snapshots and long-term compressed history."""
    retention_days: int = 90
    compression_enabled: bool = True

    entries: List[ArchiveEntry] = field(default_factory=list)

    def archive(self, memory: Memory) -> ArchiveEntry:
        """Archive a memory item."""
        content = memory.content
        original_size = len(content)

        # Simple compression (placeholder for real compression)
        if self.compression_enabled:
            compressed = content  # Would use real compression
            compressed_size = len(compressed)
        else:
            compressed = content
            compressed_size = original_size

        entry = ArchiveEntry(
            content=compressed,
            compressed=self.compression_enabled,
            original_size=original_size,
            compressed_size=compressed_size,
            metadata={
                "memory_id": str(memory.id),
                "memory_type": memory.memory_type,
            },
        )
        self.entries.append(entry)
        return entry

    def search(self, query: str, top_k: int = 5) -> List[ArchiveEntry]:
        """Search archived entries."""
        scored = []
        for entry in self.entries:
            score = 0.0
            if query.lower() in entry.content.lower():
                score += 1.0
            if score > 0:
                scored.append((entry, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_k]]

    @property
    def total_original_size(self) -> int:
        return sum(e.original_size for e in self.entries)

    @property
    def total_compressed_size(self) -> int:
        return sum(e.compressed_size for e in self.entries)

    @property
    def compression_ratio(self) -> float:
        orig = self.total_original_size
        if orig == 0:
            return 1.0
        return self.total_compressed_size / orig
