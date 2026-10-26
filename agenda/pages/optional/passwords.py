"""Passwords page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


@register
class Passwords(BasePage):
    """Passwords page with a warning, 1 page per instance.

    Top to bottom: a bordered warning box (``WARN_ROWS`` baseline rows, a triangle icon drawn
    with lines plus wrapped text), 1 gap row, a label row (Site / User / Password or hint) and
    write-in entries of ``ROW_BASELINES`` rows each in three columns separated by a gutter.
    Fit rule (``layout(rows)``): entries = ``(rows - FIXED_ROWS) // ROW_BASELINES``, never
    negative, so small pages get fewer entries instead of overflowing. ``Passwords(count=N)``
    gives N pages (default 1, repetition "1-2"); no config field yet, like Todo.
    """

    id = "passwords"
    name = "Passwords"
    category = "optional"
    section = "optional"

    WARN_ROWS = 4
    FIXED_ROWS = WARN_ROWS + 2  # warning, gap, label row
    ROW_BASELINES = 2
    COLUMNS = 3

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> int:
        """Entry rows for ``rows`` baseline rows of content."""
        return max(0, (rows - cls.FIXED_ROWS) // cls.ROW_BASELINES)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("passwords.title"))

        # Warning box: rows 0..WARN_ROWS, border, triangle icon, wrapped text.
        x, w = g.safe.x, g.safe.w
        top, bottom = g.row(0), g.row(self.WARN_ROWS)
        pdf.set_draw_color(*color(pdf, "accent"))
        pdf.set_line_width(tokens.STROKE_REGULAR)
        pdf.rect(x, top, w, bottom - top)
        icon = min(2 * g.baseline, bottom - top - 2 * g.gutter)
        ix, iy = x + g.gutter, top + (bottom - top - icon) / 2
        pdf.set_line_width(tokens.STROKE_LIGHT)
        pdf.polygon([(ix + icon / 2, iy), (ix + icon, iy + icon), (ix, iy + icon)])
        pdf.line(ix + icon / 2, iy + icon * 0.35, ix + icon / 2, iy + icon * 0.65)
        pdf.line(ix + icon / 2, iy + icon * 0.78, ix + icon / 2, iy + icon * 0.85)
        tx = ix + icon + g.gutter
        pdf.set_text_color(*color(pdf, "ink"))
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(tx, top + g.baseline / 2)
        pdf.multi_cell(
            x + w - g.gutter - tx,
            g.baseline,
            s("passwords.warning"),
            max_line_height=g.baseline,
            new_x="LEFT",
            new_y="NEXT",
        )

        col_w = (w - (self.COLUMNS - 1) * g.gutter) / self.COLUMNS
        label_row = self.WARN_ROWS + 1
        labels = (s("passwords.site"), s("passwords.user"), s("passwords.password"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_text_color(*color(pdf, "muted"))
        for c, label in enumerate(labels):
            pdf.set_xy(x + c * (col_w + g.gutter), g.row(label_row))
            pdf.cell(col_w, g.baseline, label)
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(self.layout(g.rows)):
            y = g.row(label_row + (k + 1) * self.ROW_BASELINES)
            for c in range(self.COLUMNS):
                cx = x + c * (col_w + g.gutter)
                pdf.line(cx, y, cx + col_w, y)
