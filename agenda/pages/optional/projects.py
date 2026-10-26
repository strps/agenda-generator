"""Projects page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, draw_label_rule, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx
from agenda.pages.optional._common import _draw_task_list


@register
class Projects(BasePage):
    """Project planner, 1 page per instance (one project per page).

    Top to bottom: project and objective rows, a start | deadline row, 1 gap row, the task list
    (label row + task rows) , 1 gap row and a notes block (label row + plain rules).
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure; of the rest, notes get a third
    (at least ``MIN_NOTES``) and tasks the remainder, so small pages shrink both instead of
    overflowing. ``Projects(count=N)`` gives N pages (default 1); no config field yet.
    """

    id = "projects"
    name = "Project planner"
    category = "optional"
    section = "optional"

    FIELD_ROWS = 3
    FIXED_ROWS = FIELD_ROWS + 4  # fields, gap, task labels, gap, notes label
    MIN_NOTES = 2
    LABEL_W = 22.0
    BOX = 3.0
    DUE_COLS = 1

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(task rows, notes rows) for ``rows`` baseline rows of content."""
        free = max(0, rows - cls.FIXED_ROWS)
        notes = min(free, max(cls.MIN_NOTES, free // 3))
        return free - notes, notes

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("projects.title"))

        tasks, notes = self.layout(g.rows)
        x, w = g.safe.x, g.safe.w
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        draw_label_rule(pdf, x, w, g.row(1), s("projects.name"), self.LABEL_W)
        draw_label_rule(pdf, x, w, g.row(2), s("projects.objective"), self.LABEL_W)
        span = g.columns // 2
        lx, lw = g.col(0, span)
        rx, rw = g.col(span, g.columns - span)
        draw_label_rule(pdf, lx, lw, g.row(3), s("projects.start"), self.LABEL_W)
        draw_label_rule(pdf, rx, rw, g.row(3), s("projects.deadline"), self.LABEL_W)

        tr = self.FIELD_ROWS + 1
        labels = (s("projects.task"), s("projects.due"))
        _draw_task_list(pdf, g, tr, tasks, labels, self.BOX, self.DUE_COLS)

        nr = tr + tasks + 2
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(nr))
        pdf.cell(w, g.baseline, s("projects.notes"))
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(notes):
            y = g.row(nr + 2 + k)
            pdf.line(x, y, x + w, y)
