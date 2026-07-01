from __future__ import annotations

def explain_violations(violations: list[str]) -> str:
    if not violations:
        return "All constraints satisfied."
    return " | ".join(violations)
