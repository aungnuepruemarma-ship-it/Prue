"""Skill evolution - Promote better versions, retire weak ones."""

from dataclasses import dataclass
from typing import Any, Dict

from ncp.skills.benchmark import SkillBenchmark
from ncp.skills.registry import SkillRegistry
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillEvolution:
    """Promotes better skill versions, retires weak ones."""

    registry: SkillRegistry
    benchmark: SkillBenchmark

    min_score: float = 0.5

    def evolve(self) -> Dict[str, Any]:
        """Run evolution cycle."""
        promoted = 0
        retired = 0

        for skill in self.registry.list_active():
            score = self.benchmark.score(skill)

            if score < self.min_score:
                skill.is_active = False
                retired += 1
                logger.info("Retired skill %s (score=%.2f)", skill.name, score)
            elif score > 0.8:
                promoted += 1
                skill.confidence = min(1.0, skill.confidence + 0.05)

        return {"promoted": promoted, "retired": retired}
