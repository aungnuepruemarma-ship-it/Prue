"""Capability graph — capabilities linked to the providers that serve them."""

from __future__ import annotations

from ncp.capabilities.registry import ProviderRegistry
from ncp.graph.simple import SimpleGraph


class CapabilityGraph:
    """Bipartite capability<->provider view built from the registry."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.graph = SimpleGraph()
        self.rebuild()

    def rebuild(self) -> None:
        self.graph.clear()
        for record in self.registry.all():
            self.graph.add_node(f"provider:{record.id}", {"kind": "provider", "record": record.to_dict()})
            for capability in set(record.capabilities) | set(record.preferred_tasks):
                cap_node = f"capability:{capability}"
                if cap_node not in self.graph.nodes:
                    self.graph.add_node(cap_node, {"kind": "capability"})
                self.graph.add_edge(cap_node, f"provider:{record.id}", "served_by")

    def providers_for(self, capability: str) -> list[str]:
        return [
            n.split(":", 1)[1]
            for n in self.graph.neighbors(f"capability:{capability}")
            if n.startswith("provider:")
        ]

    def capabilities(self) -> list[str]:
        return sorted(n.split(":", 1)[1] for n in self.graph.nodes if n.startswith("capability:"))
