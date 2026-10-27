"""Qt-free catalog of user-visible GUI and CLI text (English and Spanish).

Separate from agenda/i18n.py, which only holds the printed-PDF strings. Messages use dotted keys
and ``str.format`` fields. English is the source of truth and the fallback.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from agenda.uitext.en import MESSAGES as _EN
from agenda.uitext.es import MESSAGES as _ES
from agenda.uitext.es_fields import MESSAGES as _ES_FIELDS

LANGUAGES = ("en", "es")
DEFAULT = "en"
ENV_VAR = "AGENDA_UI_LANG"
_LOCALE_VARS = ("LC_ALL", "LC_MESSAGES", "LANG")
_TABLES: dict[str, Mapping[str, str]] = {"en": _EN, "es": {**_ES, **_ES_FIELDS}}

_current: str | None = None


def _from_locale(name: str | None) -> str:
    """Map a locale name such as "es_PE.UTF-8" to a UI language (anything but es* -> en)."""
    code = (name or "").strip().lower()
    for lang in LANGUAGES:
        if code == lang or code.startswith((lang + "_", lang + "-", lang + ".", lang + "@")):
            return lang
    return DEFAULT


def system_language(environ: Mapping[str, str] | None = None) -> str:
    """AGENDA_UI_LANG (en|es), else the first non-empty of LC_ALL, LC_MESSAGES, LANG, else en."""
    env = os.environ if environ is None else environ
    explicit = env.get(ENV_VAR, "").strip().lower()
    if explicit in LANGUAGES:
        return explicit
    for var in _LOCALE_VARS:
        value = env.get(var, "").strip()
        if value:
            return _from_locale(value)
    return DEFAULT


def resolve_language(pref: str | None, system_locale: str | None) -> str:
    """An explicit preference ("en"/"es") wins; "system" or None uses the system locale."""
    if pref in LANGUAGES:
        return pref
    return _from_locale(system_locale)


def startup_language(
    pref: str | None, system_locale: str | None, environ: Mapping[str, str] | None = None
) -> str:
    """GUI startup: saved preference (en/es) > AGENDA_UI_LANG > system locale > en."""
    if pref in LANGUAGES:
        return str(pref)
    env = os.environ if environ is None else environ
    explicit = env.get(ENV_VAR, "").strip().lower()
    if explicit in LANGUAGES:
        return explicit
    return resolve_language(pref, system_locale)


def set_language(lang: str) -> None:
    global _current
    if lang not in LANGUAGES:
        raise ValueError(f"unsupported UI language {lang!r}; expected one of {LANGUAGES}")
    _current = lang


def get_language() -> str:
    """The current UI language, initialized from the environment on first use."""
    global _current
    if _current is None:
        _current = system_language()
    return _current


def keys() -> frozenset[str]:
    """All catalog keys (the English table defines them)."""
    return frozenset(_EN)


def tr(key: str, **fmt: object) -> str:
    """Text for ``key`` in the current language, falling back to English."""
    text = _TABLES[get_language()].get(key)
    if text is None:
        try:
            text = _EN[key]
        except KeyError:
            raise KeyError(f"unknown UI text key: {key!r}") from None
    return text.format(**fmt) if fmt else text


def lookup(key: str) -> str | None:
    """Raw text of ``key`` in the current language (no formatting, no English fallback), or None.

    For Config field/section texts whose English source lives elsewhere; they may contain
    literal braces such as ``{n}``.
    """
    return _TABLES[get_language()].get(key)


class Table(Mapping[str, str]):
    """Read-only mapping ``key -> tr(f"{prefix}.{key}")``, resolved in the current language."""

    def __init__(self, prefix: str, keys: tuple[str, ...]) -> None:
        self._prefix = prefix
        self._keys = keys

    def __getitem__(self, key: str) -> str:
        if key not in self._keys:
            raise KeyError(key)
        return tr(f"{self._prefix}.{key}")

    def __iter__(self):
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)

    def __repr__(self) -> str:
        return f"Table({dict(self)!r})"
