"""Confidence stage — aggregate stage outcomes into a single score."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConfidenceScorer:
    base: float = 0.9
    violation_penalty: float = 0.25

    def score(self, output: dict[str, Any], violations: list[str]) -> float:
        score = self.base
        if output.get("status") not in {"success", "accepted"}:
            score -= 0.4
        score -= self.violation_penalty * len(violations)
        provider_confidence = output.get("confidence")
        if provider_confidence is not None:
            score = (score + float(provider_confidence)) / 2
        return max(0.0, min(1.0, score))
