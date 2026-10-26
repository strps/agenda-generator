"""Travel page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_checkbox,
    draw_label_rule,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


class TravelLayout(NamedTuple):
    day_rows: int  # itinerary day rows
    pack_rows: int  # packing rows per column
    pack_cols: int  # packing columns (1 or 2)


@register
class Travel(BasePage):
    """Travel planner, ``count`` pages (default 1; id ``travel``, value score 4).

    The catalog gives no repetition, so ``Travel(count=N)`` gives N pages like Todo and Media.
    Top to bottom: destination row, from | to dates row, budget row (``FIELD_ROWS``, label +
    rule), a gap, the itinerary (label row + day rows, each a short "Day N" column and a rule),
    a gap and the packing list (label row + checkbox + rule rows).

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (fields, 2 gaps, 2 labels); the
    remaining rows are split by ``ITINERARY_SHARE`` (rounded down) for the itinerary and the
    rest for packing. Packing uses two columns when the page has at least ``TWO_COL_ROWS`` rows
    (a5, letter), one on shorter pages (b6); smaller pages just get fewer rows, never overflow.
    """

    id = "travel"
    added_value = 4
    name = "Travel planner"
    category = "value_added"
    section = "value_added"

    FIELD_ROWS = 3
    FIXED_ROWS = FIELD_ROWS + 4  # fields, gap, itinerary label, gap, packing label
    ITINERARY_SHARE = 0.6
    TWO_COL_ROWS = 30
    BOX_RATIO = 0.7  # checkbox side as a fraction of a baseline row
    MAX_DAYS = 14

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> TravelLayout:
        """Itinerary day rows and packing rows/columns for ``rows`` baseline rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        days = min(cls.MAX_DAYS, int(free * cls.ITINERARY_SHARE))
        return TravelLayout(
            days, free - int(free * cls.ITINERARY_SHARE), 2 if rows >= cls.TWO_COL_ROWS else 1
        )

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("travel.title"))

        x, w = g.safe.x, g.safe.w
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        keys = ("destination", "from", "to", "budget")
        label_w = max(pdf.get_string_width(s(f"travel.{k}")) for k in keys) + g.gutter
        draw_label_rule(pdf, x, w, g.row(1), s("travel.destination"), label_w)
        span = g.columns // 2
        lx, lw = g.col(0, span)
        rx, rw = g.col(span, g.columns - span)
        draw_label_rule(pdf, lx, lw, g.row(2), s("travel.from"), label_w)
        draw_label_rule(pdf, rx, rw, g.row(2), s("travel.to"), label_w)
        draw_label_rule(pdf, x, w, g.row(3), s("travel.budget"), label_w)

        days, pack, ncols = self.layout(g.rows)
        top = self.FIELD_ROWS + 1
        small = tokens.TYPE_SIZES_PT[0]
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", small)
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("travel.itinerary"))
        pdf.set_font(font(pdf, "secondary"), "", small)
        day_w = pdf.get_string_width(f"{s('travel.day')} {self.MAX_DAYS}") + g.gutter
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(days):
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_xy(x, g.row(top + 1 + k))
            pdf.cell(day_w, g.baseline, f"{s('travel.day')} {k + 1}")
            y = g.row(top + 2 + k)
            pdf.line(x + day_w, y, x + w, y)

        top += days + 2
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", small)
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("travel.packing"))
        box = g.baseline * self.BOX_RATIO
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for c in range(ncols):
            cx, cw = g.col(c * (g.columns // ncols), g.columns // ncols)
            for k in range(pack):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                draw_checkbox(pdf, cx, ty + (g.baseline - box) / 2, box)
                pdf.line(cx + box + g.gutter / 2, y, cx + cw, y)
