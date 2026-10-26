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

from agenda import templates, themes
from agenda.config import FILLER_MODES, Config
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
TEXT, PATH, OPT_PATH, OPT_TEXT, MULTI_CHOICE, INT_LIST, TEXT_LIST, PAGES = (
    "text",
    "path",
    "opt_path",
    "opt_text",
    "multi_choice",
    "int_list",
    "text_list",
    "pages",
)

THEME, COLOR, FONT = "theme", "color", "font"
PAGE_CHOICE = "page_choice"  # a catalog page id (or a filler mode), picked from a list
PAGE_LIST = "page_list"  # catalog page ids, one checkbox per eligible page

# Fields holding a catalog page id (edited as a list of pages).
PAGE_FIELDS = ("pad_with", "weekly_filler", "daily_filler")
PAGE_LIST_FIELDS = ("month_start_pages", "month_end_pages")  # per-month pages, as checkboxes

# Fields whose list items are free-form catalog ids / texts, not literals, and the PDF style fields.
_SPECIAL = {
    "pages": PAGES,
    "daily_months": INT_LIST,
    "qr_urls": TEXT_LIST,
    "theme": THEME,
    "font_primary": FONT,
    "font_secondary": FONT,
    **{n: COLOR for n in Config.model_fields if n.startswith("color_")},
}


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


def page_choices(name: str) -> tuple[str, ...]:
    """Values ``Config`` accepts for a page-id field: any page for pad_with; the filler modes and
    single pages with no side for the fillers (the rule of ``Config._check_filler``)."""
    from agenda.catalog import all_pages  # lazy: the catalog imports Config

    if name == "pad_with":
        return tuple(p.id for p in all_pages())
    ok = [p.id for p in all_pages() if p.pages == 1 and p.starts_on == "any"]
    return (*FILLER_MODES, *ok)


def _kind(name: str, tp: Any) -> tuple[str, tuple[str, ...]]:
    if name == "theme":
        return THEME, tuple(themes.THEMES)
    if name in PAGE_FIELDS:
        return PAGE_CHOICE, page_choices(name)
    if name in PAGE_LIST_FIELDS:
        from agenda.catalog import all_pages  # lazy: the catalog imports Config

        return PAGE_LIST, tuple(p.id for p in all_pages() if p.per_month)
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
        if optional and args[0] is Path:
            return OPT_PATH, ()
        if optional and args[0] is str:
            return OPT_TEXT, ()
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
