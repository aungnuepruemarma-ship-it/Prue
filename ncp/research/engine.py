from __future__ import annotations
from dataclasses import dataclass, field

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
