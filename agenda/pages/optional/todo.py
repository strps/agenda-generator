"""Todo page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx
from agenda.pages.optional._common import _draw_task_list


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
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("todo.title"))

        _draw_task_list(
            pdf, g, 0, self.layout(g.rows), (s("todo.task"), s("todo.due")), self.BOX, self.DUE_COLS
        )
