"""Security policies applied by the verification pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SecurityPolicy:
    """Deny-list based output/action policy.

    The verification pipeline consults this before any provider output is
    committed; policies are data so deployments can tighten them.
    """

    forbidden_terms: list[str] = field(default_factory=lambda: ["rm -rf /", "DROP TABLE"])
    max_output_chars: int = 1_000_000

    def check_text(self, text: str) -> list[str]:
        violations = [f"forbidden_term:{term}" for term in self.forbidden_terms if term in text]
        if len(text) > self.max_output_chars:
            violations.append("output_too_large")
        return violations
