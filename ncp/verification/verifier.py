"""Verification pipeline.

Model Output -> Constraint Check -> Fact Check -> Consistency -> Safety
-> Confidence -> Approved. Runs on every provider output before it is
committed, independent of which provider generated it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ncp.verification.confidence import ConfidenceScorer
from ncp.verification.consistency import ConsistencyChecker
from ncp.verification.fact_checker import FactChecker
from ncp.verification.safety import SafetyChecker

Stage = Callable[[dict[str, Any], dict[str, Any]], list[str]]


@dataclass
class VerificationReport:
    approved: bool
    confidence: float
    violations: list[str] = field(default_factory=list)
    stage_results: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "confidence": self.confidence,
            "violations": self.violations,
            "stage_results": self.stage_results,
        }


def constraint_stage(output: dict[str, Any], context: dict[str, Any]) -> list[str]:
    """Surface constraint-gate rejections recorded by the execution layer."""
    violations = list(context.get("constraint_violations", []))
    if output.get("status") == "rejected":
        violations.append("constraint_gate_rejected")
    return violations


@dataclass
class Verifier:
    fact_checker: FactChecker = field(default_factory=FactChecker)
    consistency: ConsistencyChecker = field(default_factory=ConsistencyChecker)
    safety: SafetyChecker = field(default_factory=SafetyChecker)
    confidence: ConfidenceScorer = field(default_factory=ConfidenceScorer)
    min_confidence: float = 0.3
    extra_stages: dict[str, Stage] = field(default_factory=dict)

    def verify(self, output: dict[str, Any], context: dict[str, Any] | None = None) -> VerificationReport:
        context = context or {}
        stages: dict[str, Stage] = {
            "constraint": constraint_stage,
            "fact_check": self.fact_checker.check,
            "consistency": self.consistency.check,
            "safety": self.safety.check,
            **self.extra_stages,
        }
        stage_results: dict[str, list[str]] = {}
        violations: list[str] = []
        for name, stage in stages.items():
            found = stage(output, context)
            stage_results[name] = found
            violations.extend(found)
        score = self.confidence.score(output, violations)
        approved = not violations and score >= self.min_confidence
        return VerificationReport(
            approved=approved,
            confidence=score,
            violations=violations,
            stage_results=stage_results,
        )
