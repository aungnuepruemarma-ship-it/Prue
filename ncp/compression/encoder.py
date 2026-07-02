"""Encoder - Encode data into compact representations."""

from typing import Any, Dict

from ncp.compression.dictionary import CompressionDictionary


class Encoder:
    """Encodes data using dictionary-based compression."""

    def __init__(self, dictionary: CompressionDictionary = None):
        self.dictionary = dictionary or CompressionDictionary()

    def encode(self, data: Any) -> Dict[str, Any]:
        """Encode data into compact form."""
        if isinstance(data, str):
            return self._encode_string(data)
        elif isinstance(data, dict):
            return {k: self.encode(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.encode(item) for item in data]
        return data

    def _encode_string(self, text: str) -> str:
        """Encode string using dictionary substitutions."""
        result = text
        for name, pattern in self.dictionary.motifs.items():
            result = result.replace(pattern, f"${name}")
        return result
