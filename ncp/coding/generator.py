"""Code generator - Generate code candidates."""

from dataclasses import dataclass, field
from typing import List
from uuid import UUID, uuid4


@dataclass
class CodeCandidate:
    """A generated code candidate."""
    id: UUID = field(default_factory=uuid4)
    language: str = "python"
    code: str = ""
    description: str = ""
    score: float = 0.0


@dataclass
class CodeGenerator:
    """Generates code candidates and alternative implementations."""

    candidates: List[CodeCandidate] = field(default_factory=list)

    def generate(self, specification: str, language: str = "python") -> List[CodeCandidate]:
        """Generate code from specification."""
        candidate = CodeCandidate(
            language=language,
            code=f"# Generated code for: {specification}\n",
            description=specification,
            score=0.5,
        )
        self.candidates.append(candidate)
        return [candidate]

    def generate_alternatives(self, specification: str,
                              count: int = 3) -> List[CodeCandidate]:
        """Generate multiple alternative implementations."""
        return [
            CodeCandidate(
                language="python",
                code=f"# Alternative {i} for: {specification}\n",
                score=0.5 + i * 0.1,
            )
            for i in range(count)
        ]
