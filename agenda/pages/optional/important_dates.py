"""ImportantDates page."""

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
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
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
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(top))
            pdf.cell(w, g.baseline, s.month_name(m))
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            for k in range(entries):
                y = g.row(top + 2 + k)
                pdf.line(x, y, x + self.DAY_W, y)
                pdf.line(x + self.DAY_W + self.DAY_GAP, y, x + w, y)
