"""Research manager - Coordinates discovery workflow."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ncp.events.bus import EventBus
from ncp.interfaces.research import ResearchInterface
from ncp.memory.manager import MemoryManager
from ncp.research.discovery import DiscoveryEngine
from ncp.research.hypothesis import Hypothesis
from ncp.research.verification import VerificationEngine
from ncp.utils.config import Config
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ResearchManager(ResearchInterface):
    """Coordinates discovery workflow.

    Connects research to memory and skills.
    """

    memory: MemoryManager
    event_bus: EventBus
    config: Config

    discovery: DiscoveryEngine = None

    def __post_init__(self):
        if self.discovery is None:
            self.discovery = DiscoveryEngine(
                verification=VerificationEngine(),
            )

    def discover(self, context: Dict[str, Any]) -> List[Any]:
        """Run discovery loop."""
        logger.info("Running discovery with context: %s", context)

        # Generate hypothesis from context
        if "observation" in context:
            hyp = self.discovery.generate_hypothesis(
                context["observation"], context
            )

        # Run discovery
        discoveries = self.discovery.discover(context)

        # Store verified discoveries in memory
        for hyp in discoveries:
            from ncp.core.entities import Memory
            self.memory.store(Memory(
                content=hyp.statement,
                memory_type="semantic",
                confidence=hyp.confidence,
            ))

        logger.info("Discovery complete: %d verified", len(discoveries))
        return discoveries

    def hypothesize(self, observation: Any) -> Any:
        """Generate hypothesis from observation."""
        return self.discovery.generate_hypothesis(str(observation))

    def verify(self, hypothesis: Any) -> bool:
        """Verify a hypothesis."""
        if isinstance(hypothesis, Hypothesis):
            return self.discovery.verification.verify(hypothesis)
        return False
