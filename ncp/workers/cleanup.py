"""Cleanup worker - Background cleanup tasks."""

from dataclasses import dataclass
from typing import Any, Dict

from ncp.memory.manager import MemoryManager
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CleanupWorker:
    """Worker that cleans up expired memory items."""

    memory: MemoryManager

    def run(self) -> Dict[str, Any]:
        """Run cleanup."""
        logger.info("Running cleanup worker")
        removed = self.memory.working.cleanup_expired()
        return {"expired_removed": removed}
