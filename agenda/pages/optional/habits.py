"""Habits page."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_in_month
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, draw_circle, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


@register
class Habits(BasePage):
    """Monthly habit tracker, 1 page per month (12 instances): habits x days grid of circles.

    Header row (baseline row 0) holds the month title; row 1 the day numbers over the day
    columns; then one baseline row per habit. The name write-in column is the first
    ``NAME_COLS`` grid columns (plus gutter); the days of *that* month (28-31, from the calendar)
    share the remaining width equally, so cell width = remaining width / days. Each cell holds a
    small circle (``CIRCLE_RATIO`` of the smaller of cell width and row height). Weekend columns
    get the ``weekend_fill`` tint behind the grid.
    Fit rule (``layout(rows)``): habits = ``rows - HEADER_ROWS`` (title + day numbers), capped
    at ``MAX_HABITS``; never negative.
    """

    id = "habits"
    per_month = True
    name = "Habit tracker"
    category = "optional"
    section = "optional"

    HEADER_ROWS = 2
    MAX_HABITS = 20
    NAME_COLS = 2
    CIRCLE_RATIO = 0.7

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int, max_habits: int = MAX_HABITS) -> int:
        """Habit rows that fit in ``rows`` content rows, at most ``max_habits``."""
        return max(0, min(max_habits, rows - cls.HEADER_ROWS))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        month, year = ctx["month"], ctx["year"]
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("habits.title", month=s.month_name(month), year=year))

        x = g.safe.x
        days = days_in_month(year, month)
        n = self.layout(g.rows, config.habits_max)
        name_w = g.span_width(self.NAME_COLS)
        gx = x + name_w + g.gutter
        cell_w = (g.safe.x2 - gx) / days
        diam = min(cell_w, g.baseline) * self.CIRCLE_RATIO

        pdf.set_fill_color(*color(pdf, "weekend_fill"))
        for d in range(days):
            if date(year, month, d + 1).weekday() >= 5:
                pdf.rect(gx + d * cell_w, g.row(1), cell_w, (n + 1) * g.baseline, style="F")

        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(
            font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0]
        )  # regular: narrower digits
        pdf.set_xy(x, g.row(1))
        pdf.cell(name_w, g.baseline, s("habits.habit"))
        for d in range(days):
            pdf.set_xy(gx + d * cell_w, g.row(1))
            pdf.cell(cell_w, g.baseline, str(d + 1), align="C")

        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(n):
            top = g.row(2 + k)
            pdf.line(x, top + g.baseline, x + name_w, top + g.baseline)
            for d in range(days):
                draw_circle(pdf, gx + (d + 0.5) * cell_w, top + g.baseline / 2, diam)
