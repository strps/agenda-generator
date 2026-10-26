"""Fitness niche pack page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_label_rule,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import Ctx
from agenda.pages.value_added._common import _Counted


class FitnessLayout(NamedTuple):
    exercise_rows: int  # exercise rows in the log
    notes_rows: int  # rule rows under "Notes"


@register
class PackFitness(_Counted):
    """Fitness workout log, ``count`` pages (default 1; id ``niche_fitness``).

    Date row, then a heading row (exercise | sets | reps | weight) and exercise rows of
    ``ROW_BASELINES`` baselines. Columns come from the grid: exercise = 2 columns, sets = 2
    columns holding ``SET_CELLS`` small rects, reps and weight = 1 column each (a rule).
    Notes (label + rules) close the page.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` (date, heading, gap, notes label) are structure;
    notes get ``NOTES_SHARE`` of the free rows (at least ``NOTES_MIN``) and the exercise log
    takes the rest in whole ``ROW_BASELINES`` rows.
    """

    id = "niche_fitness"
    added_value = 5
    name = "Fitness pack"
    FIXED_ROWS = 4
    ROW_BASELINES = 2
    NOTES_SHARE = 0.2
    NOTES_MIN = 2
    SET_CELLS = 4
    CELL_RATIO = 1.2  # set rect height / baseline
    COLS = ((0, 2, "exercise"), (2, 2, "sets"), (4, 1, "reps"), (5, 1, "weight"))

    @classmethod
    def layout(cls, rows: int) -> FitnessLayout:
        free = max(0, rows - cls.FIXED_ROWS)
        notes = min(free, max(cls.NOTES_MIN, int(free * cls.NOTES_SHARE)))
        return FitnessLayout((free - notes) // cls.ROW_BASELINES, notes)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("fitness.title"))
        x, w = g.safe.x, g.safe.w
        ex, notes = self.layout(g.rows)
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        date = s("fitness.date")
        draw_label_rule(pdf, x, w, g.row(1), date, pdf.get_string_width(date) + g.gutter)
        for col, span, key in self.COLS:
            cx, cw = g.col(col, span)
            self._label(pdf, g, cx, cw, 2, s(f"fitness.{key}"))
        sx, sw = g.col(2, 2)
        gap = g.gutter / 2
        cell = (sw - g.gutter - gap * (self.SET_CELLS - 1)) / self.SET_CELLS
        for k in range(ex):
            bottom = 3 + (k + 1) * self.ROW_BASELINES - 1
            self._rules(pdf, g, x, w, bottom, 1)
            pdf.set_draw_color(*color(pdf, "muted"))
            pdf.set_line_width(tokens.STROKE_LIGHT)
            for c in range(self.SET_CELLS):
                pdf.rect(
                    sx + c * (cell + gap),
                    g.row(bottom) - g.baseline * self.CELL_RATIO - g.baseline * 0.1,
                    cell,
                    g.baseline * self.CELL_RATIO,
                )
        top = 3 + ex * self.ROW_BASELINES + 1
        self._label(pdf, g, x, w, top, s("fitness.notes"))
        self._rules(pdf, g, x, w, top + 2, max(0, notes - 1))
