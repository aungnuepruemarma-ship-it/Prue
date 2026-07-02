"""Execution environment description: host, plugins, budgets."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Environment:
    plugins: list[str] = field(default_factory=list)
    devices: list[str] = field(default_factory=lambda: ["cpu"])
    budgets: dict[str, float] = field(default_factory=dict)

    def register_plugin(self, name: str) -> None:
        if name not in self.plugins:
            self.plugins.append(name)

    def describe_host(self) -> dict[str, str]:
        return {
            "python": sys.version.split()[0],
            "platform": platform.system().lower(),
            "machine": platform.machine(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugins": list(self.plugins),
            "devices": list(self.devices),
            "budgets": dict(self.budgets),
            "host": self.describe_host(),
        }
