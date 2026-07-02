"""Compression dictionary - Reusable motifs, patterns, abstractions, symbols."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CompressionDictionary:
    """Stores reusable compression patterns."""

    motifs: Dict[str, str] = field(default_factory=dict)
    patterns: Dict[str, Any] = field(default_factory=dict)
    abstractions: Dict[str, str] = field(default_factory=dict)
    symbols: Dict[str, str] = field(default_factory=dict)

    def add_motif(self, name: str, pattern: str) -> None:
        self.motifs[name] = pattern

    def get_symbol(self, name: str) -> str:
        return self.symbols.get(name, name)

    def size(self) -> int:
        return len(self.motifs) + len(self.patterns) + len(self.abstractions) + len(self.symbols)
