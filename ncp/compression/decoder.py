"""Decoder - Reconstruct memory from compressed forms."""

from typing import Any

from ncp.compression.dictionary import CompressionDictionary


class Decoder:
    """Decodes compressed data back to original form."""

    def __init__(self, dictionary: CompressionDictionary = None):
        self.dictionary = dictionary or CompressionDictionary()

    def decode(self, data: Any) -> Any:
        """Decode compressed data."""
        if isinstance(data, str):
            return self._decode_string(data)
        elif isinstance(data, dict):
            return {k: self.decode(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.decode(item) for item in data]
        return data

    def _decode_string(self, text: str) -> str:
        """Decode string by expanding symbols."""
        result = text
        for name, pattern in self.dictionary.motifs.items():
            result = result.replace(f"${name}", pattern)
        return result
