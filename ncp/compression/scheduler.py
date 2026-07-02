"""Compression scheduler - Decide when to compress."""

from ncp.memory.policies import MemoryPolicies
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


class CompressionScheduler:
    """Decides when to compress and how much.

    Balances recall fidelity against storage budget.
    """

    def __init__(self, policies: MemoryPolicies = None):
        self.policies = policies or MemoryPolicies()
        self.storage_budget_mb: float = 1000.0
        self.current_usage_mb: float = 0.0

    def should_compress(self) -> bool:
        """Check if compression should run."""
        usage_ratio = self.current_usage_mb / self.storage_budget_mb
        return usage_ratio > 0.8  # Compress when 80% full

    def get_target_ratio(self) -> float:
        """Get target compression ratio based on pressure."""
        usage_ratio = self.current_usage_mb / self.storage_budget_mb
        if usage_ratio > 0.9:
            return 0.3  # Aggressive compression
        elif usage_ratio > 0.8:
            return 0.5  # Moderate
        return 0.7  # Light
