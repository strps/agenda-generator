"""Helpers shared by the value-added page modules."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.config import Config
from agenda.draw import (
    color,
    draw_header_title,
    set_font,
)
from agenda.grid import Grid
from agenda.pages.base import BasePage, Ctx


def _fit(pdf: FPDF, text: str, width: float) -> str:
    """``text`` shortened with "..." so it fits ``width`` mm in the current font."""
    if pdf.get_string_width(text) <= width:
        return text
    while text and pdf.get_string_width(text + "...") > width:
        text = text[:-1]
    return text + "..."


class _Counted(BasePage):
    """Shared ``count=N`` behaviour of the niche pack pages (default 1, negatives raise)."""

    category = "value_added"
    section = "value_added"

    def __init__(self, count: int | None = None) -> None:
        if count is not None and count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        """``count`` pages if given to the constructor, else ``config.<id>_pages``."""
        n = self.count if self.count is not None else getattr(config, f"{self.id}_pages")
        return [{} for _ in range(n)]

    @staticmethod
    def _header(pdf: FPDF, g: Grid, title: str, config: Config) -> None:
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        draw_header_title(pdf, g, title, config, tokens.TYPE_SIZES_PT[3])

    @staticmethod
    def _label(pdf: FPDF, g: Grid, x: float, w: float, row: int, text: str) -> None:
        """Small bold muted label whose text cell starts at ``g.row(row)``."""
        pdf.set_text_color(*color(pdf, "muted"))
        set_font(pdf, "primary", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(row))
        pdf.cell(w, g.baseline, text)

    @staticmethod
    def _rules(pdf: FPDF, g: Grid, x: float, w: float, first: int, n: int) -> None:
        """``n`` hairline write-in rules on lines ``first`` .. ``first + n - 1``."""
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(n):
            pdf.line(x, g.row(first + k), x + w, g.row(first + k))
