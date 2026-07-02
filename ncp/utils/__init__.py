"""NCP Utils — shared utilities for both lineages."""

from .config import Config as SystemConfig
from .config import load_config
from .exceptions import (
    ExecutionError,
    MemoryError,
    NCPError,
    RoutingError,
    StorageError,
    ValidationError,
)
from .hashing import hash_dict, hash_string
from .ids import generate_id, id_from_string, new_id
from .logger import get_logger
from .metrics import approximate_cost, candidate_text, normalized_entropy, token_overlap, tokenize
from .runtime_config import Config, RuntimeConfig
from .serializer import Serializer
from .timer import Timer, timed
from .version import parse_version

__all__ = [
    "RuntimeConfig",
    "Config",
    "SystemConfig",
    "load_config",
    "get_logger",
    "Timer",
    "timed",
    "NCPError",
    "ValidationError",
    "ExecutionError",
    "StorageError",
    "MemoryError",
    "RoutingError",
    "Serializer",
    "hash_dict",
    "hash_string",
    "generate_id",
    "id_from_string",
    "new_id",
    "parse_version",
    "approximate_cost",
    "candidate_text",
    "normalized_entropy",
    "token_overlap",
    "tokenize",
]
