"""Safety stage — applies the security policy to provider output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ncp.security.policy import SecurityPolicy


@dataclass
class SafetyChecker:
    policy: SecurityPolicy = field(default_factory=SecurityPolicy)

    def check(self, output: dict[str, Any], context: dict[str, Any]) -> list[str]:
        text = str(output.get("response", "")) + " " + str(output.get("explanation", ""))
        return self.policy.check_text(text)
