"""Skill extractor - Find repeated successful traces.

Extracts reusable workflow shapes and proposes candidate skills.
"""

from dataclasses import dataclass
from typing import List

from ncp.core.entities import Skill
from ncp.memory.episodic import EpisodicMemory
from ncp.skills.registry import SkillRegistry
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillExtractor:
    """Finds repeated successful traces and extracts skills."""

    registry: SkillRegistry
    min_occurrences: int = 3
    min_success_rate: float = 0.7

    def extract_from_episodes(self, episodic: EpisodicMemory) -> List[Skill]:
        """Extract skills from episodic memory."""
        skills = []

        # Find frequently successful task patterns
        successful = episodic.get_successful()

        # Group by task name
        from collections import Counter
        task_names = [ep.task_name for ep in successful]
        frequent = Counter(task_names).most_common()

        for task_name, count in frequent:
            if count >= self.min_occurrences:
                # Create skill from pattern
                skill = Skill(
                    name=f"skill_{task_name}",
                    trigger_patterns=[task_name],
                    workflow={"task": task_name},
                    success_count=count,
                    is_active=True,
                )
                skills.append(skill)
                self.registry.register(skill)
                logger.info("Extracted skill: %s (%d occurrences)",
                           task_name, count)

        return skills

    def should_extract(self, episodic: EpisodicMemory) -> bool:
        """Check if skill extraction should run."""
        return episodic.episode_count >= self.min_occurrences
