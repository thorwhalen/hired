"""
Configuration management using Mapping interfaces.

Implement:
- ConfigStore: MutableMapping for configuration management
- Default configurations
- Configuration merging utilities
"""

from typing import Any
from collections.abc import MutableMapping
from collections.abc import MutableMapping as ABCMutableMapping
from hired.base import RenderingConfig
from hired.util import _merge_dicts


class ConfigStore(ABCMutableMapping):
    """Configuration store with cascading defaults."""

    def __init__(self, base_config: dict | None = None):
        self._config = base_config or {}

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._config[key] = value

    def __delitem__(self, key: str) -> None:
        del self._config[key]

    def __iter__(self):
        return iter(self._config)

    def __len__(self) -> int:
        return len(self._config)


def get_default_config() -> ConfigStore:
    return ConfigStore({'format': 'pdf', 'theme': 'default'})


def load_config(path: str) -> ConfigStore:
    # Only JSON for now
    from hired.util import _load_json_file

    return ConfigStore(_load_json_file(path))
