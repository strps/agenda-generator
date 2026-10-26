"""Monthly quotes page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


@register
class MonthlyQuotes(BasePage):
    """Motivational quote per month, 1 page per month (12 instances, value score 3).

    A large quote area (``QUOTE_SHARE`` of the content rows), then a label row and write-in
    rules for the user's own reflection. The quote for month ``m`` is i18n key ``quotes.<m>``.

    Quote rule: the built-in quotes are short original sayings written for this project and
    carry no attribution. A real author is named only for a genuinely public-domain quote that
    is certain; there are none today. Add new ones as ``quotes.<n>`` keys in every language.

    Fit rule: the quote is set in the largest of ``QUOTE_SIZES`` (indices into
    ``tokens.TYPE_SIZES_PT``) whose wrapped text fits the quote area at ``LINE_ROWS`` baselines
    per line; if none fits, the smallest is used and extra lines are dropped.
    """

    id = "quotes"
    per_month = True
    added_value = 3
    name = "Monthly quotes"
    category = "value_added"
    section = "value_added"

    QUOTE_SHARE = 0.5
    QUOTE_SIZES = (4, 3, 2)
    LINE_ROWS = 2
    MIN_RULES = 1

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(quote area rows, reflection write-in rules) for ``rows`` baseline rows."""
        q = int(rows * cls.QUOTE_SHARE) // cls.LINE_ROWS * cls.LINE_ROWS
        return q, max(0, rows - q - 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("quotes.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x, w = g.safe.x, g.safe.w
        q_rows, rules = self.layout(g.rows)
        line_h = g.baseline * self.LINE_ROWS
        max_lines = max(1, q_rows // self.LINE_ROWS)
        text = s(f"quotes.{ctx['month']}")
        size = self.QUOTE_SIZES[-1]
        for size in self.QUOTE_SIZES:
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[size])
            lines = pdf.multi_cell(w, line_h, text, dry_run=True, output="LINES")
            if len(lines) <= max_lines:
                break
        lines = lines[:max_lines]
        pdf.set_text_color(*color(pdf, "ink"))
        y0 = g.row(0) + (q_rows - len(lines) * self.LINE_ROWS) / 2 * g.baseline
        for i, line in enumerate(lines):
            pdf.set_xy(x, y0 + i * line_h)
            pdf.cell(w, line_h, line)

        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(q_rows))
        pdf.cell(w, g.baseline, s("quotes.reflection"))
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(rules):
            y = g.row(q_rows + 2 + k)
            pdf.line(x, y, x + w, y)
