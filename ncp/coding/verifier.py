"""Code verifier - Verify correctness of generated code."""

from dataclasses import dataclass
from typing import List

from ncp.coding.generator import CodeCandidate
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodeVerifier:
    """Verifies code respects constraints before promotion."""

    def verify(self, candidate: CodeCandidate) -> bool:
        """Verify a code candidate."""
        # Check syntax (basic)
        if not candidate.code:
            return False

        if candidate.language == "python":
            try:
                compile(candidate.code, "<string>", "exec")
                candidate.score += 0.2
                return True
            except SyntaxError:
                logger.warning("Syntax error in generated code")
                return False

        return True

    def verify_all(self, candidates: List[CodeCandidate]) -> List[CodeCandidate]:
        """Verify multiple candidates, return valid ones."""
        return [c for c in candidates if self.verify(c)]
