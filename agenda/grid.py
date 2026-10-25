"""Layout grid: pure geometry in mm (no drawing).

A ``Grid`` describes one page: margins (by page side), header/footer bands, the content box,
``columns`` equal columns separated by gutters, and baseline rows. Rects are ``Rect(x, y, w, h)``
with the origin at the top-left of the page (fpdf2 convention).

``side`` is the physical page side: ``"right"`` (recto, odd page; binding on the left, so the
inner margin is the left one) or ``"left"`` (verso; inner margin on the right). The side swap
for alternating pages is decided by the caller (``Grid.for_page`` is the natural hook).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, NamedTuple

from agenda import tokens
from agenda.config import Config

Side = Literal["left", "right"]
_EPS = 1e-9


class Rect(NamedTuple):
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h


@dataclass(frozen=True)
class Grid:
    page_w: float
    page_h: float
    inner: float
    outer: float
    top: float = tokens.MARGIN_TOP
    bottom: float = tokens.MARGIN_BOTTOM
    header_h: float = tokens.HEADER_HEIGHT
    footer_h: float = tokens.FOOTER_HEIGHT
    columns: int = tokens.COLUMNS
    gutter: float = tokens.GUTTER
    baseline: float = tokens.BASELINE
    side: Side = "right"

    def __post_init__(self) -> None:
        if self.side not in ("left", "right"):
            raise ValueError(f"side must be 'left' or 'right', got {self.side!r}")
        if self.columns < 1 or self.baseline <= 0 or self.gutter < 0:
            raise ValueError("columns >= 1, baseline > 0, gutter >= 0 required")
        if self.col_width <= 0 or self.content.h < self.baseline:
            raise ValueError("margins leave no room for content on this page size")

    @classmethod
    def from_config(cls, cfg: Config, side: Side = "right") -> Grid:
        w, h = cfg.page_dimensions
        return cls(w, h, cfg.inner_margin, cfg.outer_margin, side=side)

    def for_side(self, side: Side) -> Grid:
        """Same grid for the other page side (hook for alternating margins)."""
        return Grid(**{**self.__dict__, "side": side})

    # --- margins / boxes -------------------------------------------------
    @property
    def left(self) -> float:
        return self.inner if self.side == "right" else self.outer

    @property
    def right(self) -> float:
        return self.outer if self.side == "right" else self.inner

    @property
    def safe(self) -> Rect:
        """Area inside the margins (header + content + footer)."""
        return Rect(
            self.left,
            self.top,
            self.page_w - self.left - self.right,
            self.page_h - self.top - self.bottom,
        )

    @property
    def header(self) -> Rect:
        s = self.safe
        return Rect(s.x, s.y, s.w, self.header_h)

    @property
    def footer(self) -> Rect:
        s = self.safe
        return Rect(s.x, s.y2 - self.footer_h, s.w, self.footer_h)

    @property
    def content(self) -> Rect:
        """Between header and footer; height is a whole number of baseline rows."""
        s = self.safe
        avail = s.h - self.header_h - self.footer_h
        return Rect(s.x, s.y + self.header_h, s.w, self.rows_in(avail) * self.baseline)

    # --- columns ---------------------------------------------------------
    @property
    def col_width(self) -> float:
        return (self.safe.w - (self.columns - 1) * self.gutter) / self.columns

    def col_x(self, i: int) -> float:
        """Left edge of column ``i`` (0-based)."""
        return self.safe.x + i * (self.col_width + self.gutter)

    def span_width(self, span: int) -> float:
        return span * self.col_width + (span - 1) * self.gutter

    def col(self, i: int, span: int = 1) -> tuple[float, float]:
        """(x, width) of ``span`` columns starting at column ``i`` (0-based)."""
        if i < 0 or span < 1 or i + span > self.columns:
            raise ValueError(f"columns {i}+{span} outside 0..{self.columns}")
        return self.col_x(i), self.span_width(span)

    # --- baseline --------------------------------------------------------
    def rows_in(self, height: float) -> int:
        return math.floor(height / self.baseline + _EPS)

    @property
    def rows(self) -> int:
        return self.rows_in(self.content.h)

    def row(self, n: int) -> float:
        """y of baseline line ``n`` (0 = top of content box)."""
        return self.content.y + n * self.baseline

    def snap(self, y: float) -> float:
        """Nearest baseline line y, relative to the content top."""
        n = round((y - self.content.y) / self.baseline)
        return self.content.y + n * self.baseline

    def span(self, col: int = 0, cols: int = 1, row: int = 0, rows: int | None = None) -> Rect:
        """Rect covering ``cols`` columns and ``rows`` baseline rows (default: to the end)."""
        if rows is None:
            rows = self.rows - row
        if row < 0 or rows < 0 or row + rows > self.rows:
            raise ValueError(f"rows {row}+{rows} outside 0..{self.rows}")
        x, w = self.col(col, cols)
        return Rect(x, self.row(row), w, rows * self.baseline)
