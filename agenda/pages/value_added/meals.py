"""Meals page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_checkbox,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


class MealsLayout(NamedTuple):
    day_rows: int  # baselines per weekday row of the planner
    grocery_rows: int  # grocery rows per column
    grocery_cols: int  # 1 or 2


@register
class Meals(BasePage):
    """Meal and grocery planner, 1 page (value score 4; the catalog gives no repetition).

    Top: the weekly planner. A label row (breakfast / lunch / dinner), then 7 weekday rows in
    ``config.week_start`` order (short localized names in a ``NAME_COLS``-wide column, the three
    meal cells share the rest, hairline-framed). Below: a gap row, a "Groceries" label row and
    checkbox + item rules, in ``GROCERY_COLS`` columns when the page has at least
    ``TWO_COL_ROWS`` rows, else one column.

    Fit rule (``layout(rows)``): the planner gets ``PLANNER_SHARE`` of the rows, spent as 1
    label row plus 7 days of ``day_rows`` baselines (1..``MAX_DAY_ROWS``). Groceries get what is
    left after the gap and label rows, so small pages get fewer grocery rows, never overflow.
    """

    id = "meals"
    added_value = 4
    name = "Meal and grocery planner"
    category = "value_added"
    section = "value_added"

    MEALS = ("breakfast", "lunch", "dinner")
    DAYS = 7
    PLANNER_SHARE = 0.6
    MAX_DAY_ROWS = 4
    NAME_COLS = 1
    TWO_COL_ROWS = 30
    BOX = 3.0

    @classmethod
    def layout(cls, rows: int) -> MealsLayout:
        """Planner day height and grocery rows per column for ``rows`` baseline rows."""
        day_rows = max(1, min(cls.MAX_DAY_ROWS, (int(rows * cls.PLANNER_SHARE) - 1) // cls.DAYS))
        rest = max(0, rows - (1 + cls.DAYS * day_rows) - 2)
        return MealsLayout(day_rows, rest, 2 if rows >= cls.TWO_COL_ROWS else 1)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("meals.title"))

        day_rows, per_col, ncols = self.layout(g.rows)
        x = g.safe.x
        gx = x + g.span_width(self.NAME_COLS) + g.gutter
        cell_w = (g.safe.x2 - gx) / len(self.MEALS)
        row_h = day_rows * g.baseline

        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        for i, key in enumerate(self.MEALS):
            pdf.set_xy(gx + i * cell_w, g.row(0))
            pdf.cell(cell_w, g.baseline, s(f"meals.{key}"), align="C")
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for d, name in enumerate(s.weekday_names(config.week_start, "short")):
            y = g.row(1) + d * row_h
            pdf.set_xy(x, y)
            pdf.cell(gx - x - g.gutter, row_h, name)
            for i in range(len(self.MEALS)):
                pdf.rect(gx + i * cell_w, y, cell_w, row_h)

        top = 1 + self.DAYS * day_rows + 1
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(top))
        pdf.cell(g.safe.w, g.baseline, s("meals.groceries"))
        box = min(self.BOX, g.baseline - 1.0)
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for c in range(ncols):
            cx, cw = g.col(c * (g.columns // ncols), g.columns // ncols)
            for k in range(per_col):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                draw_checkbox(pdf, cx, ty + (g.baseline - box) / 2, box)
                pdf.line(cx + box + 2, y, cx + cw, y)
