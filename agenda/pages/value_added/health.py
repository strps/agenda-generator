"""Health tracker page."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_in_month
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    MOOD_LEVELS,
    color,
    draw_checkbox,
    draw_circle,
    draw_mood,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


@register
class HealthTracker(BasePage):
    """Monthly health tracker, 1 page per month (12 instances, value score 4).

    Row 0-1: the mood legend, the 5 drawn faces (``draw_mood`` levels 1 very sad to 5 very
    happy) each with its level number, after a "Mood" label. Row ``LEGEND_ROWS + GAP_ROWS``
    holds the day numbers; below it, one tracker row of ``ROW_ROWS`` baselines per entry of
    ``TRACKERS`` (mood, water, sleep, exercise, other). The label column is the first
    ``NAME_COLS`` grid columns; the days of *that* month (28-31) share the rest equally, one
    hairline-framed cell per day per row. Cell content: mood a circle to mark or number, water
    ``GLASSES`` stacked small circles, sleep an empty cell for the hours, exercise a checkbox,
    other an empty cell. Weekend columns get the ``weekend_fill`` tint.

    Fit rule (``layout(rows)``): the cells are never shrunk below ``ROW_ROWS`` baselines
    high; instead trackers are dropped from the end of ``TRACKERS`` when the page is short
    (b6 keeps all of them at 2 baselines per row). Never negative.
    """

    id = "health"
    per_month = True
    added_value = 4
    name = "Health tracker"
    category = "value_added"
    section = "value_added"

    TRACKERS = ("mood", "water", "sleep", "exercise", "other")
    LEGEND_ROWS = 2
    GAP_ROWS = 1
    DAYS_ROWS = 1
    ROW_ROWS = 2
    NAME_COLS = 2
    GLASSES = 4
    FACE_RATIO = 0.8  # legend face diameter as a fraction of LEGEND_ROWS baselines
    MARK_RATIO = 0.7  # in-cell mark size as a fraction of the smaller of cell width and height

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> int:
        """Number of tracker rows (leading entries of ``TRACKERS``) that fit in ``rows``."""
        free = rows - cls.LEGEND_ROWS - cls.GAP_ROWS - cls.DAYS_ROWS
        return max(0, min(len(cls.TRACKERS), free // cls.ROW_ROWS))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        month, year = ctx["month"], ctx["year"]
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("health.title", month=s.month_name(month), year=year))

        x = g.safe.x
        days = days_in_month(year, month)
        n = self.layout(g.rows)
        name_w = g.span_width(self.NAME_COLS)
        gx = x + name_w + g.gutter
        cell_w = (g.safe.x2 - gx) / days
        row_h = g.baseline * self.ROW_ROWS

        # mood legend: label, then the five faces with their level numbers
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        ly = g.row(0)
        pdf.set_xy(x, ly)
        pdf.cell(name_w, g.baseline * self.LEGEND_ROWS, s("health.mood"))
        face = g.baseline * self.LEGEND_ROWS * self.FACE_RATIO
        slot = (g.safe.x2 - gx) / len(MOOD_LEVELS)
        for i, level in enumerate(MOOD_LEVELS):
            fx = gx + i * slot
            draw_mood(pdf, fx + face / 2, ly + g.baseline * self.LEGEND_ROWS / 2, face, level)
            pdf.set_xy(fx + face + g.gutter / 2, ly)
            pdf.cell(slot - face, g.baseline * self.LEGEND_ROWS, str(level))

        top = g.row(self.LEGEND_ROWS + self.GAP_ROWS)
        grid_h = self.DAYS_ROWS * g.baseline + n * row_h
        pdf.set_fill_color(*color(pdf, "weekend_fill"))
        for d in range(days):
            if date(year, month, d + 1).weekday() >= 5:
                pdf.rect(gx + d * cell_w, top, cell_w, grid_h, style="F")
            pdf.set_xy(gx + d * cell_w, top)
            pdf.cell(cell_w, g.baseline, str(d + 1), align="C")

        mark = min(cell_w, row_h) * self.MARK_RATIO
        for k, key in enumerate(self.TRACKERS[:n]):
            y = top + g.baseline * self.DAYS_ROWS + k * row_h
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_xy(x, y)
            pdf.cell(name_w, row_h, s(f"health.{key}"))
            for d in range(days):
                cx = gx + (d + 0.5) * cell_w
                pdf.set_draw_color(*color(pdf, "line"))
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.rect(gx + d * cell_w, y, cell_w, row_h)
                if key == "mood":
                    draw_circle(pdf, cx, y + row_h / 2, mark)
                elif key == "water":
                    pitch = row_h / self.GLASSES
                    for q in range(self.GLASSES):
                        draw_circle(pdf, cx, y + (q + 0.5) * pitch, min(mark, pitch * 0.7))
                elif key == "exercise":
                    draw_checkbox(pdf, cx - mark / 2, y + (row_h - mark) / 2, mark)
