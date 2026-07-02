"""Memory policies - Retention, novelty, consolidation thresholds."""

from dataclasses import dataclass


@dataclass
class MemoryPolicies:
    """Configuration for memory operations.

    - Retention thresholds
    - Novelty thresholds
    - Consolidation thresholds
    - Decay settings
    """
    # Retention
    min_importance: float = 0.1
    min_confidence: float = 0.1
    max_age_hours: float = 168  # 1 week

    # Novelty
    novelty_threshold: float = 0.5
    similarity_threshold: float = 0.85

    # Consolidation
    consolidation_min_episodes: int = 3
    consolidation_interval_hours: float = 1.0
    replay_sample_size: int = 5

    # Decay
    decay_rate: float = 0.01
    importance_boost: float = 0.1

    # Retrieval
    top_k_default: int = 10
    multi_scale: bool = True
