"""Qt-free settings logic: field specs derived from ``Config``, values <-> Config <-> YAML.

No rules live here: ``build_config`` hands raw values to ``Config`` and reports its errors.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agenda import templates
from agenda.config import Config
from agenda.configfile import ConfigFileError, load_yaml

# widget kinds
BOOL, CHOICE, OPT_CHOICE, INT, FLOAT, AUTO_INT = (
    "bool",
    "choice",
    "opt_choice",
    "int",
    "float",
    "auto_int",
)
TEXT, PATH, MULTI_CHOICE, INT_LIST, TEXT_LIST, PAGES = (
    "text",
    "path",
    "multi_choice",
    "int_list",
    "text_list",
    "pages",
)

# Fields whose list items are free-form catalog ids / texts, not literals.
_SPECIAL = {"pages": PAGES, "daily_months": INT_LIST, "qr_urls": TEXT_LIST}


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str
    choices: tuple[str, ...] = ()
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None


def _literals(tp: Any) -> tuple[str, ...]:
    return tuple(typing.get_args(tp))


def _kind(name: str, tp: Any) -> tuple[str, tuple[str, ...]]:
    if name in _SPECIAL:
        return _SPECIAL[name], ()
    origin = typing.get_origin(tp)
    if origin is typing.Literal:
        return CHOICE, _literals(tp)
    if origin in (types.UnionType, typing.Union):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        optional = len(typing.get_args(tp)) > len(args) and len(args) == 1
        if optional and typing.get_origin(args[0]) is typing.Literal:
            return OPT_CHOICE, _literals(args[0])
        if int in args:
            return AUTO_INT, ()
    if origin is list:
        (item,) = typing.get_args(tp)
        return MULTI_CHOICE, _literals(item)
    if tp is bool:
        return BOOL, ()
    if tp is int:
        return INT, ()
    if tp is float:
        return FLOAT, ()
    if tp is Path:
        return PATH, ()
    return TEXT, ()


def _bound(info: Any, attr: str) -> float | None:
    for m in info.metadata:
        if hasattr(m, attr):
            return getattr(m, attr)
    return None


def field_specs() -> list[FieldSpec]:
    """One spec per ``Config`` field, in declaration order."""
    specs = []
    for name, info in Config.model_fields.items():
        kind, choices = _kind(name, info.annotation)
        lo = _bound(info, "ge")
        hi = _bound(info, "le")
        specs.append(
            FieldSpec(name, kind, choices, info.get_default(call_default_factory=True), lo, hi)
        )
    return specs


def default_values() -> dict[str, Any]:
    return {s.name: s.default for s in field_specs()}


def parse_lines(text: str) -> list[str]:
    """One entry per non-empty line (qr_urls)."""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def build_config(values: dict[str, Any]) -> tuple[Config | None, str]:
    """Validate ``values`` with ``Config``. Returns ``(config, "")`` or ``(None, message)``."""
    try:
        return Config(**values), ""
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            msg = "; ".join(
                f"{'.'.join(str(p) for p in e['loc']) or 'config'}: {e['msg']}"
                for e in exc.errors()
            )
        else:
            msg = str(exc)
        return None, msg


def config_to_data(cfg: Config) -> dict[str, Any]:
    """Plain YAML-ready mapping of every set field (``None`` values omitted)."""
    data = cfg.model_dump(mode="json")
    return {k: v for k, v in data.items() if v is not None}


def config_to_yaml_data(cfg: Config) -> dict[str, Any]:
    """Grouped form: global fields flat, section fields under their block, empty blocks omitted."""
    out: dict[str, Any] = {}
    for name, value in config_to_data(cfg).items():
        spec = templates.section(templates.group_of(name))
        if spec.block is None:
            out[name] = value
            continue
        short = next(k for k, f in spec.fields.items() if f == name)
        out.setdefault(spec.block, {})[short] = value
    return out


def save_yaml(cfg: Config, path: Path | str) -> None:
    text = yaml.safe_dump(config_to_yaml_data(cfg), sort_keys=False, allow_unicode=True)
    Path(path).write_text(text, encoding="utf-8")


def load_values(path: Path | str) -> dict[str, Any]:
    """YAML file -> full values dict (defaults for missing keys). Unknown keys are kept so that
    ``Config`` rejects them when the values are built."""
    return {**default_values(), **load_yaml(path)}


__all__ = [
    "ConfigFileError",
    "FieldSpec",
    "build_config",
    "config_to_data",
    "config_to_yaml_data",
    "default_values",
    "field_specs",
    "load_values",
    "parse_lines",
    "save_yaml",
]
