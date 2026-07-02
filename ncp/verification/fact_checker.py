"""Fact-check stage — provider claims must not contradict world state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FactChecker:
    def check(self, output: dict[str, Any], context: dict[str, Any]) -> list[str]:
        facts: dict[str, Any] = context.get("world_facts", {})
        claims: dict[str, Any] = output.get("claims", {})
        violations = []
        for key, claimed in claims.items():
            if key in facts and str(facts[key]) != str(claimed):
                violations.append(f"fact_contradiction:{key}:claimed={claimed}:known={facts[key]}")
        return violations
