"""Optional pages."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import draw_checkbox, draw_label_rule
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx

_ACCENT = tokens.COLORS["accent"]


@register
class Goals(BasePage):
    """Yearly goals, 1 page: per goal a title rule, checkbox steps and a deadline rule.

    Fit rule (``layout(rows)``): a block is title + steps + deadline + 1 gap row. Try 6 goals,
    then 5, with the most steps (at most ``MAX_STEPS``) that fit; accept the first count that
    leaves at least ``MIN_STEPS`` steps. Small pages therefore get fewer steps, then 5 goals.
    """

    id = "goals"
    name = "Yearly goals"
    category = "optional"
    section = "optional"

    MAX_STEPS = 4
    MIN_STEPS = 2
    GOAL_COUNTS = (6, 5)
    LABEL_W = 22.0
    BOX = 3.0

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(goals, steps per goal) for ``rows`` baseline rows of content."""
        for n in cls.GOAL_COUNTS:
            steps = min(cls.MAX_STEPS, rows // n - 3)
            if steps >= cls.MIN_STEPS:
                return n, steps
        n = cls.GOAL_COUNTS[-1]
        return n, max(0, min(cls.MAX_STEPS, rows // n - 3))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("goals.title"))

        goals, steps = self.layout(g.rows)
        block = steps + 3
        x, w = g.safe.x, g.safe.w
        box = min(self.BOX, g.baseline - 1.0)
        for i in range(goals):
            r = i * block
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
            draw_label_rule(pdf, x, w, g.row(r + 1), s("goals.goal", n=i + 1), self.LABEL_W)
            pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
            for k in range(steps):
                top, y = g.row(r + 1 + k), g.row(r + 2 + k)
                draw_checkbox(pdf, x, top + (g.baseline - box) / 2, box)
                pdf.set_draw_color(*tokens.COLORS["line"])
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.line(x + box + 2, y, x + w, y)
            draw_label_rule(pdf, x, w, g.row(r + 2 + steps), s("goals.deadline"), self.LABEL_W)


@register
class ImportantDates(BasePage):
    """Birthdays and anniversaries, 1 page: 12 month blocks in 2 columns x 6 rows.

    Fit rule (``layout(rows)``): each of the 6 block rows gets ``rows // 6`` baseline rows;
    one is the month title and one is the gap, the rest are write-in rows (day + name), at
    least 1. Small pages therefore get fewer write-in rows instead of overflowing.
    """

    id = "important_dates"
    name = "Important dates"
    category = "optional"
    section = "optional"

    BLOCK_COLS = 2
    BLOCK_ROWS = 6
    MIN_ENTRIES = 1
    DAY_W = 8.0
    DAY_GAP = 2.0

    @classmethod
    def layout(cls, rows: int) -> int:
        """Write-in rows per month for ``rows`` baseline rows of content."""
        return max(cls.MIN_ENTRIES, rows // cls.BLOCK_ROWS - 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("dates.title"))

        entries = self.layout(g.rows)
        per = entries + 2
        span = g.columns // self.BLOCK_COLS
        for m in range(1, 13):
            r, c = divmod(m - 1, self.BLOCK_COLS)
            x, w = g.col(c * span, span)
            top = r * per
            pdf.set_text_color(*_ACCENT)
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(top))
            pdf.cell(w, g.baseline, s.month_name(m))
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            for k in range(entries):
                y = g.row(top + 2 + k)
                pdf.line(x, y, x + self.DAY_W, y)
                pdf.line(x + self.DAY_W + self.DAY_GAP, y, x + w, y)


@register
class Todo(BasePage):
    """To-do list, 1 page per instance: checkbox + task rule + due-date rule on every row.

    Single column on every size (two columns would make rules too short on b6/a5). Row 1 holds
    the column labels; every following baseline row (``layout(rows)``) is a task row, so the
    page is filled from b6 to letter. The due column is the last grid column, the task rule
    runs from the checkbox to the gutter before it. ``Todo(count=N)`` gives N pages (default 1);
    there is no config field for the count yet, like Notes/Contacts.
    """

    id = "todo"
    name = "To-do list"
    category = "optional"
    section = "optional"

    BOX = 3.0
    DUE_COLS = 1

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @staticmethod
    def layout(rows: int) -> int:
        """Task rows for ``rows`` baseline rows of content (one row is the label row)."""
        return max(0, rows - 1)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("todo.title"))

        x = g.safe.x
        dx, dw = g.col(g.columns - self.DUE_COLS, self.DUE_COLS)
        task_w = dx - g.gutter - x
        box = min(self.BOX, g.baseline - 1.0)
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(0))
        pdf.cell(task_w, g.baseline, s("todo.task"))
        pdf.set_xy(dx, g.row(0))
        pdf.cell(dw, g.baseline, s("todo.due"))
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(self.layout(g.rows)):
            top, y = g.row(1 + k), g.row(2 + k)
            draw_checkbox(pdf, x, top + (g.baseline - box) / 2, box)
            pdf.line(x + box + 2, y, x + task_w, y)
            pdf.line(dx, y, dx + dw, y)
