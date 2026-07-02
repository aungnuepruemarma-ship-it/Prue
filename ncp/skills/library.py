"""Skill library - Skill lookup and reuse."""

from dataclasses import dataclass
from typing import List, Optional

from ncp.core.entities import Skill
from ncp.skills.registry import SkillRegistry


@dataclass
class SkillLibrary:
    """Skill lookup for planner/router reuse."""

    registry: SkillRegistry

    def find_skill(self, task_description: str) -> Optional[Skill]:
        """Find skill matching task description."""
        candidates = self.registry.find_by_name(task_description)
        if candidates:
            # Return best match
            return max(candidates, key=lambda s: s.confidence)
        return None

    def list_skills(self) -> List[Skill]:
        """List all available skills."""
        return list(self.registry.skills.values())
