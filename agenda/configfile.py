"""YAML config files: load, flatten the nested ``booklet:`` block, merge under CLI overrides.

No rules live here. Keys are mapped to ``Config`` field names and everything (including unknown
keys, which ``Config`` forbids) is validated once by ``Config(**merged)``.
"""

from pathlib import Path
from typing import Any

import yaml

from agenda.templates import SECTIONS

# plan §8.3 nested block -> flat Config fields
BOOKLET_KEYS = {"size": "booklet_size", "unit": "booklet_unit", "folded": "booklet_folded"}


class ConfigFileError(ValueError):
    """The file cannot be read or is not a mapping of config settings."""


def _flatten_block(out: dict[str, Any], name: str, block: Any, keys: dict[str, str]) -> None:
    if not isinstance(block, dict):
        raise ConfigFileError(f"'{name}' must be a mapping with {', '.join(keys)}")
    for key, value in block.items():
        field = keys.get(key)
        if field is None:
            raise ConfigFileError(f"unknown key '{name}.{key}' (expected: {', '.join(keys)})")
        if field in out:
            raise ConfigFileError(f"'{name}.{key}' and '{field}' are both set")
        out[field] = value


def flatten(data: dict[str, Any]) -> dict[str, Any]:
    """Replace the nested ``booklet:`` and section blocks (``daily:``, ``notes:``, ...) by flat
    Config field names (``booklet_size``, ``daily_months``, ...)."""
    blocks = {"booklet": BOOKLET_KEYS, **{s.block: s.fields for s in SECTIONS if s.block}}
    out = {k: v for k, v in data.items() if k not in blocks}
    for name, keys in blocks.items():
        if data.get(name) is not None:
            _flatten_block(out, name, data[name], keys)
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
