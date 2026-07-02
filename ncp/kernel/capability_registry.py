"""Kernel-facing capability registry: default providers for this install.

Wraps :mod:`ncp.capabilities` and registers the reasoners that actually
exist in this deployment as constraint-selectable providers. Nothing in
the system names a provider directly — the scheduler selects through
these records.
"""

from __future__ import annotations

import os

from ncp.capabilities.graph import CapabilityGraph
from ncp.capabilities.registry import ProviderRecord, ProviderRegistry
from ncp.capabilities.selector import ProviderSelector

__all__ = ["ProviderRecord", "ProviderRegistry", "CapabilityGraph", "ProviderSelector", "build_default_registry"]


def build_default_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(ProviderRecord(
        id="rule_reasoner",
        provider="ncp",
        backend="rule",
        capabilities=["plan", "create", "update", "merge", "relate", "query", "skill"],
        preferred_tasks=["plan", "update", "query", "execute"],
        context_window=0,
        latency=0.01,
        cost=0.0,
        reliability=0.95,
    ))
    registry.register(ProviderRecord(
        id="claude_llm",
        provider="anthropic",
        backend="llm",
        repo="api://anthropic/claude-opus-4-8",
        capabilities=["research", "find", "search", "compare", "summarize", "create"],
        preferred_tasks=["research"],
        modalities=["text"],
        context_window=1_000_000,
        tool_support=True,
        latency=2.0,
        cost=1.0,
        availability=1.0 if os.environ.get("ANTHROPIC_API_KEY") else 0.5,
        reliability=0.9,
    ))
    registry.register(ProviderRecord(
        id="mythos_executable",
        provider="external",
        backend="mythos",
        capabilities=["code", "program", "build", "implement", "execute"],
        preferred_tasks=["execute", "build"],
        latency=1.0,
        cost=0.5,
        availability=0.5,  # requires a configured executable; falls back to rules
        reliability=0.85,
    ))
    return registry
