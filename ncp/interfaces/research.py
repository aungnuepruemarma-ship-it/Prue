"""Research Interface - Discovery engine."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ResearchInterface(ABC):
    """Abstract interface for research/discovery subsystem.

    Runs hypothesis generation, simulation, verification, ranking.
    """

    @abstractmethod
    def discover(self, context: Dict[str, Any]) -> List[Any]:
        """Run discovery loop.

        Args:
            context: Discovery context

        Returns:
            List of discoveries
        """
        ...

    @abstractmethod
    def hypothesize(self, observation: Any) -> Any:
        """Generate hypothesis from observation.

        Args:
            observation: Observation to base hypothesis on

        Returns:
            Generated hypothesis
        """
        ...

    @abstractmethod
    def verify(self, hypothesis: Any) -> bool:
        """Verify a hypothesis.

        Args:
            hypothesis: Hypothesis to verify

        Returns:
            True if verified
        """
        ...
