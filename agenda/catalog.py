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
