"""Student niche pack page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import Ctx
from agenda.pages.value_added._common import _Counted


class StudentLayout(NamedTuple):
    table_rows: int  # course rows in the tracker table
    study: bool  # whether the study-hours block fits


@register
class PackStudent(_Counted):
    """Student course/exam tracker, ``count`` pages (default 1; id ``niche_student``).

    A heading row (course | exam or assignment | date | grade / weight) and course rows of
    ``ROW_BASELINES`` baselines filling the page, then a study-hours block (title, 7 weekday
    labels and 7 write-in boxes of ``STUDY_BOX_ROWS`` rows).

    Fit rule (``layout(rows)``): the study block takes ``STUDY_ROWS`` plus a gap; the table gets
    the rest after its heading row, in whole ``ROW_BASELINES`` rows. Pages too short for the
    block (rows < ``STUDY_ROWS + 5``) drop it and use all rows for the table.
    """

    id = "niche_student"
    added_value = 5
    name = "Student pack"
    ROW_BASELINES = 2
    STUDY_BOX_ROWS = 2
    STUDY_ROWS = STUDY_BOX_ROWS + 2  # title, weekday labels, boxes
    COLS = ((0, 2, "course"), (2, 2, "exam"), (4, 1, "date"), (5, 1, "grade"))
    DAYS = 7

    @classmethod
    def layout(cls, rows: int) -> StudentLayout:
        study = rows >= cls.STUDY_ROWS + 5
        free = rows - 1 - (cls.STUDY_ROWS + 1 if study else 0)
        return StudentLayout(max(0, free // cls.ROW_BASELINES), study)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("student.title"))
        x, w = g.safe.x, g.safe.w
        table, study = self.layout(g.rows)
        for col, span, key in self.COLS:
            cx, cw = g.col(col, span)
            self._label(pdf, g, cx, cw, 0, s(f"student.{key}"))
        for k in range(table):
            self._rules(pdf, g, x, w, 1 + (k + 1) * self.ROW_BASELINES - 1, 1)
        if not study:
            return
        top = 1 + table * self.ROW_BASELINES + 1
        self._label(pdf, g, x, w, top, s("student.study"))
        gap = g.gutter / 2
        bw = (w - gap * (self.DAYS - 1)) / self.DAYS
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_LIGHT)
        days = s.weekday_names(config.week_start, "short")
        for d in range(self.DAYS):
            bx = x + d * (bw + gap)
            self._label(pdf, g, bx, bw, top + 1, days[d])
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_LIGHT)
            pdf.rect(bx, g.row(top + 2), bw, self.STUDY_BOX_ROWS * g.baseline)
