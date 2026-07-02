"""Confidence scoring model."""

from dataclasses import dataclass


@dataclass
class ConfidenceModel:
    """Confidence scoring for memory and results."""
    base_confidence: float = 1.0
    source_reliability: float = 1.0
    evidence_strength: float = 1.0
    verification_count: int = 0

    def compute(self) -> float:
        """Compute overall confidence."""
        confidence = self.base_confidence
        confidence *= self.source_reliability
        confidence *= self.evidence_strength
        # Boost for verified items
        confidence = min(1.0, confidence + 0.05 * self.verification_count)
        return confidence
