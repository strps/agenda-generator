"""YAML config files: load, flatten the nested ``booklet:`` block, merge under CLI overrides.

No rules live here. Keys are mapped to ``Config`` field names and everything (including unknown
keys, which ``Config`` forbids) is validated once by ``Config(**merged)``.
"""

from pathlib import Path
from typing import Any

import yaml

# plan §8.3 nested block -> flat Config fields
BOOKLET_KEYS = {"size": "booklet_size", "unit": "booklet_unit", "folded": "booklet_folded"}


class ConfigFileError(ValueError):
    """The file cannot be read or is not a mapping of config settings."""


def flatten(data: dict[str, Any]) -> dict[str, Any]:
    """Replace ``booklet: {size, unit, folded}`` by ``booklet_size`` / ``booklet_unit`` / ..."""
    out = {k: v for k, v in data.items() if k != "booklet"}
    block = data.get("booklet")
    if block is None:
        return out
    if not isinstance(block, dict):
        raise ConfigFileError("'booklet' must be a mapping with size, unit and folded")
    for key, value in block.items():
        field = BOOKLET_KEYS.get(key)
        if field is None:
            raise ConfigFileError(
                f"unknown key 'booklet.{key}' (expected: {', '.join(BOOKLET_KEYS)})"
            )
        if field in out:
            raise ConfigFileError(f"'booklet.{key}' and '{field}' are both set")
        out[field] = value
    return out


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Read a config file into flat ``Config`` kwargs (empty file -> ``{}``)."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigFileError(f"cannot read config file {path}: {exc.strerror or exc}") from None
    except yaml.YAMLError as exc:
        raise ConfigFileError(f"invalid YAML in {path}: {exc}") from None
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigFileError(f"{path}: top level must be a mapping of settings")
    return flatten(data)


def merge(yaml_values: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """CLI overrides win over YAML values, key by key."""
    return {**yaml_values, **overrides}
