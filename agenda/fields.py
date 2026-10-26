"""Qt-free access to the per-field help and CLI metadata stored on ``Config``.

Texts live only on the Config fields (``Field(description=...)`` and
``json_schema_extra={"detail": ..., "cli": {...}}``). The ``cli`` dict keys:
``flags`` (option strings; omitted = derived ``--<name-with-dashes>``, plus ``--no-`` form for
bools), ``type`` (CLI type override, e.g. "str"), ``csv`` (comma list), ``skip`` (hand-written
in cli.py).
"""

from __future__ import annotations

from typing import Any

from agenda.config import Config


def field_names() -> list[str]:
    """Config field names in declaration order."""
    return list(Config.model_fields)


def _extra(name: str) -> dict[str, Any]:
    extra = Config.model_fields[name].json_schema_extra
    return extra if isinstance(extra, dict) else {}


def short_help(name: str) -> str:
    """One-phrase help text of a field."""
    return Config.model_fields[name].description or ""


def detail_help(name: str) -> str:
    """Detailed explanation of a field (cross-field rules included)."""
    return str(_extra(name).get("detail", ""))


def cli_meta(name: str) -> dict[str, Any]:
    """CLI metadata of a field (see module docstring); a copy."""
    return dict(_extra(name).get("cli", {}))
