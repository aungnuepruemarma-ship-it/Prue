"""Configuration management.

Everything configurable. Never hardcode constants.
"""

import json
import os

try:
    import yaml
except ImportError:  # pyyaml is an optional extra; JSON configs always work
    yaml = None
from dataclasses import dataclass, field
from typing import Any, Dict

from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Config:
    """Configuration container.

    Loads from YAML files and environment variables.
    """
    _data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from a YAML (or JSON) file."""
        with open(path) as f:
            if yaml is not None:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls(data or {})

    @classmethod
    def from_env(cls, prefix: str = "NCP_") -> "Config":
        """Load configuration from environment variables."""
        data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split("_")
                current = data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
        return cls(data)

    @classmethod
    def load(cls, config_dir: str = "configs") -> "Config":
        """Load all configuration files."""
        config = cls()
        if os.path.exists(config_dir):
            for filename in sorted(os.listdir(config_dir)):
                is_yaml = filename.endswith((".yaml", ".yml"))
                is_json = filename.endswith(".json")
                if (is_yaml and yaml is not None) or is_json:
                    filepath = os.path.join(config_dir, filename)
                    logger.debug("Loading config: %s", filepath)
                    with open(filepath) as f:
                        data = yaml.safe_load(f) if is_yaml else json.load(f)
                        if data:
                            config.merge(data)
        config.merge(Config.from_env()._data)
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key."""
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot-separated key."""
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def merge(self, other: Dict[str, Any]) -> None:
        """Merge another configuration dict."""
        self._data = _deep_merge(self._data, other)

    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()


def _deep_merge(base: Dict, update: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_dir: str = "configs") -> Config:
    """Load configuration from directory."""
    return Config.load(config_dir)
