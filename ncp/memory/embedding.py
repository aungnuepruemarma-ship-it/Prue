"""Deterministic text embeddings via feature hashing (stdlib only).

Every word token and character trigram is hashed into one of ``dims``
buckets with a hash-derived sign, and the resulting vector is
L2-normalized. Cosine similarity between two such vectors genuinely
reflects lexical and sub-word overlap — related texts land measurably
closer than unrelated ones — without any model download or third-party
dependency. A learned-model backend can replace this behind the same
``embed()`` signature (future ``[embeddings]`` extra).
"""

from __future__ import annotations

import math
import re
import zlib

DEFAULT_DIMS = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _features(text: str) -> list[str]:
    """Word tokens plus character trigrams (sub-word signal for morphology)."""
    tokens = _TOKEN_RE.findall(text.lower())
    features = list(tokens)
    for token in tokens:
        padded = f"#{token}#"
        features.extend(padded[i:i + 3] for i in range(len(padded) - 2))
    return features


def embed(text: str, dims: int = DEFAULT_DIMS) -> list[float]:
    """Embed text into a dense L2-normalized vector of length ``dims``."""
    vector = [0.0] * dims
    for feature in _features(text):
        digest = zlib.crc32(feature.encode("utf-8"))
        bucket = digest % dims
        sign = 1.0 if (digest >> 31) & 1 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two embeddings (vectors are pre-normalized)."""
    return sum(x * y for x, y in zip(a, b))
