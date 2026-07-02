"""Extended provider registry.

Providers describe themselves with rich records (capabilities, modalities,
resources, cost, reliability, historical success) so the scheduler selects
by constraints rather than hardcoded names.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ProviderRecord:
    id: str
    provider: str = ""
    backend: str = ""
    repo: str = ""
    checkpoint: str = ""
    quantization: str = ""
    precision: str = ""
    capabilities: list[str] = field(default_factory=list)
    modalities: list[str] = field(default_factory=lambda: ["text"])
    languages: list[str] = field(default_factory=lambda: ["en"])
    context_window: int = 0
    tokenizer: str = ""
    tool_support: bool = False
    vision_support: bool = False
    audio_support: bool = False
    gpu_memory: float = 0.0
    cpu_memory: float = 0.0
    throughput: float = 0.0
    latency: float = 1.0
    cost: float = 0.0
    availability: float = 1.0
    reliability: float = 1.0
    historical_success: float = 0.5
    preferred_tasks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities or capability in self.preferred_tasks


class ProviderRegistry:
    def __init__(self):
        self.providers: dict[str, ProviderRecord] = {}

    def register(self, record: ProviderRecord) -> None:
        self.providers[record.id] = record

    def get(self, provider_id: str) -> ProviderRecord | None:
        return self.providers.get(provider_id)

    def all(self) -> list[ProviderRecord]:
        return list(self.providers.values())

    def find(self, capability: str | None = None, modality: str | None = None,
             min_context: int = 0, available_only: bool = True) -> list[ProviderRecord]:
        out = []
        for record in self.providers.values():
            if available_only and record.availability <= 0:
                continue
            if capability and not record.supports(capability):
                continue
            if modality and modality not in record.modalities:
                continue
            if record.context_window and record.context_window < min_context:
                continue
            out.append(record)
        return out

    def record_outcome(self, provider_id: str, success: bool, smoothing: float = 0.1) -> None:
        """Exponentially update a provider's historical success rate."""
        record = self.providers.get(provider_id)
        if record is None:
            return
        target = 1.0 if success else 0.0
        record.historical_success = (1 - smoothing) * record.historical_success + smoothing * target

    def to_dict(self) -> dict[str, Any]:
        return {pid: record.to_dict() for pid, record in self.providers.items()}
