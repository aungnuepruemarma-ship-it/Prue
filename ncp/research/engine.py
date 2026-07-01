from __future__ import annotations

from dataclasses import dataclass, field

RESEARCH_TERMS = {"research", "find", "search", "compare", "investigate"}

def is_research_goal(goal: str) -> bool:
    return bool(RESEARCH_TERMS & {t.lower() for t in goal.split()})

@dataclass
class ResearchFinding:
    source: str
    concept: str
    confidence: float = 0.5
    notes: str = ""

@dataclass
class ResearchEngine:
    findings: list[ResearchFinding] = field(default_factory=list)

    def add_finding(self, source: str, concept: str, confidence: float = 0.5, notes: str = "") -> None:
        self.findings.append(ResearchFinding(source=source, concept=concept, confidence=confidence, notes=notes))

    def record_step(self, goal: str, chosen: str, explanation: str = "") -> bool:
        """Record a finding when an accepted step served a research goal."""
        if not is_research_goal(goal):
            return False
        self.add_finding(source=goal, concept=chosen, confidence=0.6, notes=explanation)
        return True

    def to_dict(self) -> list[dict]:
        return [
            {"source": f.source, "concept": f.concept, "confidence": f.confidence, "notes": f.notes}
            for f in self.findings
        ]
