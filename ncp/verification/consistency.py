"""Consistency stage — the output record must be internally coherent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConsistencyChecker:
    def check(self, output: dict[str, Any], context: dict[str, Any]) -> list[str]:
        violations = []
        status = output.get("status")
        if status in {"success", "accepted"} and output.get("error"):
            violations.append("inconsistent:success_with_error")
        if status in {"failed", "error"} and not (output.get("error") or output.get("explanation")):
            violations.append("inconsistent:failure_without_reason")
        for key in ("entity_count", "relation_count"):
            value = output.get(key)
            if value is not None and int(value) < 0:
                violations.append(f"inconsistent:negative_{key}")
        return violations
