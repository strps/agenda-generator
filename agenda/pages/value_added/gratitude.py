"""Gratitude page."""

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
from agenda.pages.base import BasePage, Ctx


class GratitudeLayout(NamedTuple):
    lines: int  # write-in rows per block (grateful, best moment)
    last_lines: int  # write-in rows of the final "intention" block (takes the remainder)


@register
class Gratitude(BasePage):
    """Gratitude journal, ``count`` pages (default 1; value score 4, the catalog gives no repetition).

    Header: title plus a "Date" write-in field on the first content row. Then ``GRATEFUL_BLOCKS``
    numbered "I am grateful for..." blocks (label row + numbered write-in rules, the number drawn
    as small muted text in a one-baseline column), a "Best moment of the day" block and a final
    "Intention for tomorrow" block, all with plain rules. Blocks are separated by one empty row.

    Fit rule (``layout(rows)``): fixed rows = date row + one label row per block + one gap row
    between blocks; the rest is split evenly in ``lines`` write-in rows per block (at least 1,
    so b6 gets 3 and letter more), and the remainder goes to the final block. Numbering
    continues across a block's rows. ``Gratitude(count=N)`` gives N pages; there is no config
    field for the count yet, like Todo.
    """

    id = "gratitude"
    added_value = 4
    name = "Gratitude journal"
    category = "value_added"
    section = "value_added"

    GRATEFUL_BLOCKS = 3
    BLOCKS = GRATEFUL_BLOCKS + 2
    DATE_COLS = 2

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> GratitudeLayout:
        """Write-in rows per block and for the last block, for ``rows`` baseline rows."""
        fixed = 1 + cls.BLOCKS + (cls.BLOCKS - 1)
        lines = max(1, (rows - fixed) // cls.BLOCKS)
        return GratitudeLayout(lines, max(1, rows - fixed - lines * (cls.BLOCKS - 1)))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("gratitude.title"))

        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        label = s("gratitude.date")
        dx, dw = g.col(g.columns - self.DATE_COLS, self.DATE_COLS)
        draw_label_rule(pdf, dx, dw, g.row(1), label, pdf.get_string_width(label) + g.gutter)

        lines, last = self.layout(g.rows)
        x, num_w = g.safe.x, g.baseline
        top = 1
        for b in range(self.BLOCKS):
            n = last if b == self.BLOCKS - 1 else lines
            key = (
                "gratitude.grateful"
                if b < self.GRATEFUL_BLOCKS
                else ("gratitude.best" if b == self.GRATEFUL_BLOCKS else "gratitude.intention")
            )
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(x, g.row(top))
            pdf.cell(g.safe.w, g.baseline, s(key))
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            for k in range(n):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                if b < self.GRATEFUL_BLOCKS:
                    pdf.set_text_color(*color(pdf, "muted"))
                    pdf.set_xy(x, ty)
                    pdf.cell(num_w, g.baseline, str(k + 1))
                pdf.line(x + num_w, y, g.safe.x2, y)
            top += 1 + n + 1
