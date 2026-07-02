"""Consolidation worker - Background memory consolidation."""

from dataclasses import dataclass
from typing import Any, Dict

from ncp.memory.manager import MemoryManager
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsolidationWorker:
    """Worker that triggers memory consolidation."""

    memory: MemoryManager

    def run(self) -> Dict[str, Any]:
        """Run consolidation."""
        logger.info("Running consolidation worker")
        self.memory.consolidate()
        return {"status": "completed"}
