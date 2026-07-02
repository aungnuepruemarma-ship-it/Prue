"""Verification engine - Verify candidate discoveries.

Neuro-symbolic verification gates so only verified knowledge enters memory.
"""

from dataclasses import dataclass
from typing import List

from ncp.research.hypothesis import Hypothesis
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VerificationEngine:
    """Verifies hypotheses and rejects invalid results."""

    min_confidence: float = 0.7

    def verify(self, hypothesis: Hypothesis) -> bool:
        """Verify a hypothesis."""
        # Check confidence threshold
        if hypothesis.confidence < self.min_confidence:
            logger.info("Hypothesis %s rejected: confidence %.2f < %.2f",
                       hypothesis.id, hypothesis.confidence, self.min_confidence)
            return False

        # Check evidence count
        if len(hypothesis.evidence) < 1:
            logger.info("Hypothesis %s rejected: no evidence", hypothesis.id)
            return False

        hypothesis.status = "verified"
        logger.info("Hypothesis %s verified", hypothesis.id)
        return True

    def check_consistency(self, hypothesis: Hypothesis,
                          existing: List[Hypothesis]) -> bool:
        """Check if hypothesis is consistent with existing knowledge."""
        for other in existing:
            if other.statement == hypothesis.statement and other.status == "verified":
                return False  # Duplicate
        return True
