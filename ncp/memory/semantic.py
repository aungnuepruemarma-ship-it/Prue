"""Semantic memory - Distilled facts, concepts, abstractions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ncp.utils.timeutils import utcnow


@dataclass
class Concept:
    """A concept in semantic memory."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    related_concepts: List[UUID] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    embeddings: Optional[List[float]] = None


@dataclass
class SemanticMemory:
    """Stores distilled facts, concepts, and abstractions.

    Long-term knowledge base with structured concepts.
    """
    max_concepts: int = 5000
    similarity_threshold: float = 0.85

    concepts: Dict[UUID, Concept] = field(default_factory=dict)
    name_index: Dict[str, UUID] = field(default_factory=dict)

    def add_concept(self, name: str, description: str = "",
                    facts: List[str] = None,
                    confidence: float = 1.0) -> Concept:
        """Add a concept to semantic memory."""
        if name in self.name_index:
            # Update existing
            concept_id = self.name_index[name]
            concept = self.concepts[concept_id]
            if description:
                concept.description = description
            if facts:
                concept.facts.extend(facts)
            concept.confidence = confidence
            concept.updated_at = utcnow()
            return concept

        concept = Concept(
            name=name,
            description=description,
            facts=facts or [],
            confidence=confidence,
        )
        self.concepts[concept.id] = concept
        self.name_index[name] = concept.id

        # Enforce limit
        if len(self.concepts) > self.max_concepts:
            oldest = min(self.concepts.items(),
                        key=lambda x: x[1].updated_at)
            del self.concepts[oldest[0]]
            del self.name_index[oldest[1].name]

        return concept

    def get_concept(self, name: str) -> Optional[Concept]:
        """Get concept by name."""
        concept_id = self.name_index.get(name)
        if concept_id:
            return self.concepts.get(concept_id)
        return None

    def search(self, query: str, top_k: int = 10) -> List[Concept]:
        """Search concepts by name/description."""
        scored = []
        query_lower = query.lower()
        for concept in self.concepts.values():
            score = 0.0
            if query_lower in concept.name.lower():
                score += 2.0
            if query_lower in concept.description.lower():
                score += 1.0
            for fact in concept.facts:
                if query_lower in fact.lower():
                    score += 0.5
            if score > 0:
                scored.append((concept, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    @property
    def concept_count(self) -> int:
        return len(self.concepts)
