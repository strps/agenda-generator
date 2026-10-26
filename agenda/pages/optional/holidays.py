"""Holidays page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, font, merged_holidays
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx
from agenda.pages.optional._common import _ellipsize


@register
class Holidays(BasePage):
    """Public holidays of ``config.year`` for ``config.holiday_country``, 1 page.

    One row (``ROW_BASELINES`` baselines tall) per holiday: short date + name, hairline below.
    Fit rule (``layout(rows, n)``): capacity ``cap = rows // ROW_BASELINES``. If the ``n`` holidays
    fit, one column; otherwise two columns (filled top to bottom, left first) showing the first
    ``min(n, 2 * cap)`` holidays; the rest are truncated, never drawn outside the safe area.
    No holidays (or an unsupported country code) => ``cap`` empty write-in rows (date + name).
    """

    id = "holidays"
    name = "Holidays"
    category = "optional"
    section = "optional"

    ROW_BASELINES = 2

    @classmethod
    def layout(cls, rows: int, n: int) -> tuple[int, int, int]:
        """(columns, shown, rows per column) for ``n`` holidays on ``rows`` content rows."""
        cap = rows // cls.ROW_BASELINES
        if n <= 0:
            return 1, 0, cap
        if n <= cap:
            return 1, n, n
        shown = min(n, 2 * cap)
        return 2, shown, -(-shown // 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        try:
            found = list(merged_holidays(config).items())
        except ValueError:
            found = []
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, f"{s('holidays.title')} {config.year} {config.holiday_country}".strip())

        cols, shown, per_col = self.layout(g.rows, len(found))
        rh = self.ROW_BASELINES
        col_w = (g.safe.w - (cols - 1) * g.gutter * 2) / cols if cols > 1 else g.safe.w
        date_w = g.col_width
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for i in range(max(shown, per_col)):
            c, k = divmod(i, per_col)
            x = g.safe.x + c * (col_w + g.gutter * 2)
            top, y = g.row(k * rh), g.row(k * rh + rh)
            pdf.line(x, y, x + col_w, y)
            if i >= shown:
                continue
            d, name = found[i]
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            mon = s.month_name(d.month, short=True)
            when = f"{d.day} {mon.lower()}" if config.language == "es" else f"{mon} {d.day}"
            pdf.set_xy(x, top + (rh - 1) * g.baseline)
            pdf.cell(date_w, g.baseline, when)
            pdf.set_text_color(*color(pdf, "ink"))
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[1])
            nw = col_w - date_w - g.gutter
            pdf.set_xy(x + date_w + g.gutter, top + (rh - 1) * g.baseline)
            pdf.cell(nw, g.baseline, _ellipsize(pdf, name, nw))
