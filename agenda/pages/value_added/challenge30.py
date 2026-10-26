"""30-day challenge page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_circle,
    draw_label_rule,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


class ChallengeLayout(NamedTuple):
    cols: int  # day cell columns
    grid_rows: int  # day cell rows (cols * grid_rows >= DAYS)
    cell_rows: int  # baselines per day cell
    reflect_rows: int  # write-in rules under the "Reflection" label


@register
class Challenge30(BasePage):
    """30-day challenge, ``count`` pages (default 1; id ``challenges30``, value score 4).

    The catalog gives no repetition, so ``Challenge30(count=N)`` gives N pages like Todo and
    Travel. Top to bottom: "My challenge" and "Why" label + rule rows, a gap, exactly 30 day
    cells (small day number in the top-left corner, a circle to tick), a gap and a
    "Reflection" label with write-in rules over the remaining rows.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (2 fields, 2 gaps, the label);
    the grid must leave ``MIN_REFLECT_ROWS`` rules. Grid shapes are ``COLS`` (5 x 6 or 6 x 5;
    both tile 30 exactly). The tallest ``cell_rows`` (``MAX_CELL_ROWS`` down to
    ``MIN_CELL_ROWS`` baselines) that fits wins, ties go to fewer columns (wider cells).
    Cells are as wide as the safe width allows (gutter between cells), so b6 keeps six
    ~15 mm cells. Rows left over become reflection rules.
    """

    id = "challenges30"
    added_value = 4
    name = "30-day challenges"
    category = "value_added"
    section = "value_added"

    DAYS = 30
    COLS = (5, 6)
    FIELD_ROWS = 2
    FIXED_ROWS = FIELD_ROWS + 3  # fields, gap, gap, reflection label
    MIN_REFLECT_ROWS = 2
    MIN_CELL_ROWS = 2
    MAX_CELL_ROWS = 4
    CIRCLE_RATIO = 0.8  # tick circle diameter as a fraction of a baseline

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> ChallengeLayout:
        """Grid shape and reflection rules for ``rows`` baseline rows."""
        avail = rows - cls.FIXED_ROWS - cls.MIN_REFLECT_ROWS
        for cell_rows in range(cls.MAX_CELL_ROWS, cls.MIN_CELL_ROWS - 1, -1):
            for cols in cls.COLS:
                nrows = -(-cls.DAYS // cols)
                if nrows * cell_rows <= avail:
                    free = rows - cls.FIXED_ROWS - nrows * cell_rows
                    return ChallengeLayout(cols, nrows, cell_rows, free)
        cols = cls.COLS[-1]
        return ChallengeLayout(cols, -(-cls.DAYS // cols), cls.MIN_CELL_ROWS, 0)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("challenge.title"))

        x, w = g.safe.x, g.safe.w
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        label_w = (
            max(pdf.get_string_width(s(k)) for k in ("challenge.mine", "challenge.why")) + g.gutter
        )
        draw_label_rule(pdf, x, w, g.row(1), s("challenge.mine"), label_w)
        draw_label_rule(pdf, x, w, g.row(2), s("challenge.why"), label_w)

        lay = self.layout(g.rows)
        top = self.FIELD_ROWS + 1
        cw = (w - (lay.cols - 1) * g.gutter) / lay.cols
        ch = lay.cell_rows * g.baseline
        d = g.baseline * self.CIRCLE_RATIO
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        for k in range(self.DAYS):
            r, c = divmod(k, lay.cols)
            cx = x + c * (cw + g.gutter)
            cy = g.row(top + 1) + r * ch
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            pdf.rect(cx, cy, cw, ch)
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_xy(cx + g.gutter / 3, cy)
            pdf.cell(cw / 2, g.baseline, str(k + 1))
            draw_circle(pdf, cx + cw / 2, cy + (ch + g.baseline) / 2, d)

        top += 1 + lay.grid_rows * lay.cell_rows + 1
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("challenge.reflection"))
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(lay.reflect_rows):
            y = g.row(top + 2 + k)
            pdf.line(x, y, x + w, y)
