"""Consolidation manager - Move traces from short-term to long-term.

Hippocampal-style fast buffer, slow neocortical store, replay-based consolidation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from ncp.events.bus import EventBus
from ncp.memory.episodic import EpisodicMemory
from ncp.memory.replay import ReplayBuffer
from ncp.memory.semantic import SemanticMemory
from ncp.memory.skill import SkillMemory
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsolidationManager:
    """Manages memory consolidation.

    Moves traces from short-term to long-term storage.
    Replays selected episodes and updates semantic/skill memory.
    """
    replay_buffer: ReplayBuffer
    episodic: EpisodicMemory
    semantic: SemanticMemory
    skill_memory: SkillMemory
    event_bus: EventBus
    config: Config

    consolidation_count: int = field(default=0, repr=False)

    def consolidate(self) -> Dict[str, Any]:
        """Run consolidation cycle.

        1. Sample episodes from replay buffer
        2. Extract patterns and facts
        3. Update semantic memory
        4. Extract skills if patterns are reusable
        """
        logger.info("Starting consolidation cycle %d", self.consolidation_count)

        # 1. Sample episodes for replay
        samples = self.replay_buffer.sample(
            n=self.config.get("memory.consolidation.replay_count", 5),
            strategy="mixed",
        )

        if not samples:
            logger.debug("No episodes to consolidate")
            return {"consolidated": 0}

        # 2. Extract patterns and update semantic memory
        facts_extracted = 0
        for episode in samples:
            if episode.success:
                # Extract simple facts from successful episodes
                fact = f"Successfully executed: {episode.task_name}"
                self.semantic.add_concept(
                    name=episode.task_name,
                    description=fact,
                    facts=[fact],
                )
                facts_extracted += 1

        # 3. Clear replay buffer
        self.replay_buffer.clear()

        self.consolidation_count += 1

        result = {
            "consolidated": len(samples),
            "facts_extracted": facts_extracted,
            "cycle": self.consolidation_count,
        }

        logger.info("Consolidation complete: %s", result)
        return result

    def should_consolidate(self) -> bool:
        """Check if consolidation should run."""
        return self.replay_buffer.size >= self.config.get(
            "memory.consolidation.min_episodes", 3
        )
