"""Compression statistics tracking."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ncp.utils.timeutils import utcnow


@dataclass
class CompressionStatistics:
    """Tracks compression performance metrics."""

    total_compressions: int = 0
    total_decompressions: int = 0
    total_original_size: int = 0
    total_compressed_size: int = 0
    fidelity_loss_total: float = 0.0
    reuse_count: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record_compression(self, original_size: int, compressed_size: int,
                          fidelity_loss: float = 0.0) -> None:
        self.total_compressions += 1
        self.total_original_size += original_size
        self.total_compressed_size += compressed_size
        self.fidelity_loss_total += fidelity_loss
        self.history.append({
            "type": "compression",
            "original_size": original_size,
            "compressed_size": compressed_size,
            "ratio": compressed_size / original_size if original_size > 0 else 1.0,
            "fidelity_loss": fidelity_loss,
            "timestamp": utcnow().isoformat(),
        })

    @property
    def compression_ratio(self) -> float:
        if self.total_original_size == 0:
            return 1.0
        return self.total_compressed_size / self.total_original_size

    @property
    def average_fidelity_loss(self) -> float:
        if self.total_compressions == 0:
            return 0.0
        return self.fidelity_loss_total / self.total_compressions

    @property
    def storage_savings(self) -> float:
        if self.total_original_size == 0:
            return 0.0
        return 1.0 - self.compression_ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_compressions": self.total_compressions,
            "compression_ratio": round(self.compression_ratio, 4),
            "average_fidelity_loss": round(self.average_fidelity_loss, 4),
            "storage_savings": round(self.storage_savings, 4),
            "reuse_count": self.reuse_count,
        }
