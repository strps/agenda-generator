"""Registry of available pages.

Page modules decorate their classes with ``@register``. They import this module, so the catalog
imports them lazily (on first lookup) to avoid an import cycle.
"""

from __future__ import annotations

import importlib
from typing import TypeVar

from agenda.config import Config
from agenda.pages.base import CATEGORIES, BasePage

T = TypeVar("T", bound=type[BasePage])

CATALOG: dict[str, type[BasePage]] = {}  # insertion order = registration order

# Presets select non-core pages by their ``added_value`` score (plan section 3.3, 1-5). Pages
# without a score (0: core and optional pages) are only in "premium".
ESSENTIAL_MIN_VALUE = 5
COMPLETE_MIN_VALUE = 4
PRESET_MIN_VALUE: dict[str, int] = {
    "essential": ESSENTIAL_MIN_VALUE,
    "complete": COMPLETE_MIN_VALUE,
    "premium": 0,
}

PAGE_MODULES = ("agenda.pages.core", "agenda.pages.optional", "agenda.pages.value_added")


def register(cls: T) -> T:
    """Class decorator: add a BasePage subclass to the registry under its ``id``."""
    if not (isinstance(cls, type) and issubclass(cls, BasePage)):
        raise TypeError(f"@register expects a BasePage subclass, got {cls!r}")
    if cls.id in CATALOG:
        raise ValueError(
            f"duplicate page id {cls.id!r}: {CATALOG[cls.id].__name__} and {cls.__name__}"
        )
    CATALOG[cls.id] = cls
    return cls


def load_pages() -> None:
    """Import the page modules so their decorators run (idempotent)."""
    for name in PAGE_MODULES:
        importlib.import_module(name)


def get_page(page_id: str) -> type[BasePage]:
    load_pages()
    try:
        return CATALOG[page_id]
    except KeyError:
        raise KeyError(
            f"unknown page id {page_id!r}; valid ids: {', '.join(CATALOG) or '(none)'}"
        ) from None


def all_pages() -> list[type[BasePage]]:
    """All registered page classes, in registration order."""
    load_pages()
    return list(CATALOG.values())


def pages_by_category(category: str) -> list[type[BasePage]]:
    if category not in CATEGORIES:
        raise ValueError(f"unknown category {category!r}; valid: {', '.join(CATEGORIES)}")
    return [p for p in all_pages() if p.category == category]


def resolve_pages(config: Config) -> list[type[BasePage]]:
    """Page classes selected by ``config.pages`` (None = all core pages), in the given order."""
    if config.pages is None:
        return pages_by_category("core")
    return [get_page(i) for i in config.pages]


def preset_pages(name: str) -> list[str]:
    """Ids of the non-core pages a preset selects, by ``added_value`` score.

    ``essential`` = score >= ``ESSENTIAL_MIN_VALUE``, ``complete`` = score >= ``COMPLETE_MIN_VALUE``,
    ``premium`` = every registered non-core page (including unscored ones, score 0). Core pages
    are always in the plan and never listed. Order = registration order (optional pages, then
    value-added), so the lists are nested: essential <= complete <= premium.
    """
    try:
        minimum = PRESET_MIN_VALUE[name]
    except KeyError:
        raise ValueError(
            f"unknown preset {name!r}; valid presets: {', '.join(PRESET_MIN_VALUE)}"
        ) from None
    return [p.id for p in all_pages() if p.category != "core" and p.added_value >= minimum]


def catalog_rows() -> list[dict[str, object]]:
    """One row per registered page: id, name, category, value score and the presets containing it.

    Sorted by category (``CATEGORIES`` order), then value score (high first), then id. Core pages
    are in every plan, so their ``presets`` is empty.
    """
    rows = []
    for p in all_pages():
        presets = [n for n in PRESET_MIN_VALUE if p.id in preset_pages(n)]
        rows.append(
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "value": p.added_value,
                "presets": presets,
            }
        )
    rows.sort(key=lambda r: (CATEGORIES.index(str(r["category"])), -int(r["value"]), r["id"]))  # type: ignore[call-overload]
    return rows


def format_catalog(rows: list[dict[str, object]]) -> str:
    """Render ``catalog_rows`` as an aligned text table (value ``-`` = unscored)."""
    head = ("ID", "CATEGORY", "VALUE", "PRESETS", "NAME")
    body = [
        (
            str(r["id"]),
            str(r["category"]),
            str(r["value"]) if r["value"] else "-",
            ",".join(r["presets"]) if r["presets"] else "-",  # type: ignore[call-overload]
            str(r["name"]),
        )
        for r in rows
    ]
    widths = [max(len(line[i]) for line in [head, *body]) for i in range(4)]
    lines = [head, *body]
    return "\n".join(
        "  ".join(cell.ljust(w) for cell, w in zip(line[:4], widths)) + "  " + line[4]
        for line in lines
    )
