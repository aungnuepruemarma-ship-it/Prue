"""Compression manager - Coordinates all compression operations.

Blueprint: dynamic and policy-based, not a single algorithm.
Uses rate-distortion to decide how much to compress.
Cooperates with consolidation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from ncp.compression.decoder import Decoder
from ncp.compression.delta import DeltaCompressor
from ncp.compression.dictionary import CompressionDictionary
from ncp.compression.encoder import Encoder
from ncp.compression.prototype import PrototypeCompressor
from ncp.compression.scheduler import CompressionScheduler
from ncp.compression.statistics import CompressionStatistics
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CompressionManager:
    """Decides what to compress, chooses mode, coordinates encode/decode.

    Connects compression to memory consolidation.
    """

    dictionary: CompressionDictionary = field(default_factory=CompressionDictionary)
    encoder: Encoder = field(default=None)
    decoder: Decoder = field(default=None)
    statistics: CompressionStatistics = field(default_factory=CompressionStatistics)
    prototype_compressor: PrototypeCompressor = field(default_factory=PrototypeCompressor)
    delta_compressor: DeltaCompressor = field(default_factory=DeltaCompressor)
    scheduler: CompressionScheduler = field(default_factory=CompressionScheduler)

    def __post_init__(self):
        if self.encoder is None:
            self.encoder = Encoder(self.dictionary)
        if self.decoder is None:
            self.decoder = Decoder(self.dictionary)

    def compress(self, data: Any, mode: str = "auto") -> Dict[str, Any]:
        """Compress data using appropriate mode.

        Modes: auto, dictionary, prototype, delta, abstraction
        """
        import json

        original = json.dumps(data) if not isinstance(data, str) else data
        original_size = len(original)

        if mode == "auto":
            mode = self._select_mode(data)

        if mode == "dictionary":
            compressed = self.encoder.encode(data)
        elif mode == "prototype":
            proto = self.prototype_compressor.find_prototype(original)
            compressed = {"prototype": str(proto.id) if proto else None, "data": data}
        elif mode == "delta":
            deltas = self.delta_compressor.compute_delta(data if isinstance(data, dict) else {})
            compressed = {"deltas": [d.__dict__ for d in deltas]}
        else:
            compressed = data

        compressed_str = json.dumps(compressed)
        compressed_size = len(compressed_str)

        self.statistics.record_compression(original_size, compressed_size)

        logger.debug("Compressed: %d -> %d bytes (%.1f%%)",
                     original_size, compressed_size,
                     (1 - compressed_size / original_size) * 100 if original_size > 0 else 0)

        return {
            "data": compressed,
            "mode": mode,
            "original_size": original_size,
            "compressed_size": compressed_size,
        }

    def decompress(self, compressed: Dict[str, Any]) -> Any:
        """Decompress data."""
        data = compressed.get("data", compressed)
        mode = compressed.get("mode", "dictionary")

        self.statistics.total_decompressions += 1

        if mode == "dictionary":
            return self.decoder.decode(data)
        return data

    def _select_mode(self, data: Any) -> str:
        """Select best compression mode for data."""
        if isinstance(data, dict):
            return "dictionary"
        elif isinstance(data, str):
            return "prototype"
        return "dictionary"

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return self.statistics.to_dict()
