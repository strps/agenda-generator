"""BasePage base class: the contract every page type implements.

A page type declares class attributes and implements two methods:

* ``instances(config) -> list[ctx]``: one ctx per occurrence of the page (12 months, one per week,
  ...). A ctx is a plain ``dict`` of whatever ``draw`` needs (e.g. ``{"year": 2026, "month": 3}``).
  The default is a single empty ctx.
* ``draw(pdf, ctx, config, grids)``: draws ONE instance. The caller (assembler) has already added
  ``pages`` pages via ``exporter.add_page`` and passes their grids in page order (``grids[0]`` is
  the first page; ``pdf.page`` is the last added one). A spread draws on page ``pdf.page - 1`` by
  setting ``pdf.page`` itself. Pages never call ``add_page`` and never insert fillers.

``starts_on`` tells the planner which side the first page must be on ("any" = no constraint).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from fpdf import FPDF

from agenda.config import Config
from agenda.grid import Grid

CATEGORIES = ("core", "optional", "value_added")
SECTIONS = ("front_back", "monthly", "weekly", "daily", "optional", "value_added")
STARTS_ON = ("any", "left", "right")

Ctx = dict[str, Any]


class BasePage(ABC):
    id: ClassVar[str]
    name: ClassVar[str]
    category: ClassVar[str]
    section: ClassVar[str]
    pages: ClassVar[int] = 1
    starts_on: ClassVar[str] = "any"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Intermediate abstract bases may omit attributes; concrete classes must be complete.
        # (__abstractmethods__ is not set yet at this point, so inspect draw directly.)
        if not getattr(cls.draw, "__isabstractmethod__", False):
            validate_page_class(cls)

    def instances(self, config: Config) -> list[Ctx]:
        """Contexts to draw, in order. Default: one empty context."""
        return [{}]

    @abstractmethod
    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        """Draw one instance onto its ``pages`` pages (see module docstring)."""


def validate_page_class(cls: type[BasePage]) -> None:
    """Raise ValueError if the class attributes are missing or invalid."""
    for attr in ("id", "name", "category", "section"):
        value = getattr(cls, attr, None)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{cls.__name__}.{attr} must be a non-empty string")
    if cls.category not in CATEGORIES:
        raise ValueError(f"{cls.__name__}.category {cls.category!r} not in {CATEGORIES}")
    if cls.section not in SECTIONS:
        raise ValueError(f"{cls.__name__}.section {cls.section!r} not in {SECTIONS}")
    if cls.starts_on not in STARTS_ON:
        raise ValueError(f"{cls.__name__}.starts_on {cls.starts_on!r} not in {STARTS_ON}")
    if isinstance(cls.pages, bool) or not isinstance(cls.pages, int) or cls.pages < 1:
        raise ValueError(f"{cls.__name__}.pages must be an int >= 1, got {cls.pages!r}")


def month_ctxs(config: Config) -> list[Ctx]:
    """One context per month of ``config.year``: ``{"month": 1..12, "year": year}``."""
    return [{"month": m, "year": config.year} for m in range(1, 13)]
