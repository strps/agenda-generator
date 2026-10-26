"""Budget page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


@register
class Budget(BasePage):
    """Monthly budget, 1 page per month (12 instances): sections and a summary block.

    Sections in order: income, fixed expenses, variable expenses, savings. Each is a label row
    (section name, "Amount" over the amount column) then write-in rows of description rule +
    amount rule; the amount column is the last ``AMOUNT_COLS`` grid columns. A gap row follows
    each section, then the summary: total income, total expenses, balance (label + amount rule).
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (4 labels, 4 gaps, 3 summary rows);
    the rest is split by ``WEIGHTS`` (rounded down, leftovers go to the heaviest sections first),
    so small pages get fewer write-in rows instead of overflowing.
    """

    id = "budget"
    per_month = True
    name = "Monthly budget"
    category = "optional"
    section = "optional"

    WEIGHTS = (1, 2, 2, 1)
    SUMMARY_ROWS = 3
    FIXED_ROWS = len(WEIGHTS) * 2 + SUMMARY_ROWS
    AMOUNT_COLS = 2

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int, int, int]:
        """Write-in rows for (income, fixed, variable, savings) given ``rows`` content rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        total = sum(cls.WEIGHTS)
        counts = [free * wt // total for wt in cls.WEIGHTS]
        left = free - sum(counts)
        for i in sorted(range(len(counts)), key=lambda i: -cls.WEIGHTS[i]):
            if left <= 0:
                break
            counts[i] += 1
            left -= 1
        return counts[0], counts[1], counts[2], counts[3]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("budget.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x = g.safe.x
        ax, aw = g.col(g.columns - self.AMOUNT_COLS, self.AMOUNT_COLS)
        desc_w = ax - g.gutter - x
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)

        r = 0
        keys = ("income", "fixed", "variable", "savings")
        for key, n in zip(keys, self.layout(g.rows), strict=True):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(r))
            pdf.cell(desc_w, g.baseline, s(f"budget.{key}"))
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(ax, g.row(r))
            pdf.cell(aw, g.baseline, s("budget.amount"))
            for k in range(n):
                y = g.row(r + 2 + k)
                pdf.line(x, y, x + desc_w, y)
                pdf.line(ax, y, ax + aw, y)
            r += n + 2

        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        for k, key in enumerate(("total_income", "total_expenses", "balance")):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_xy(x, g.row(r + k))
            pdf.cell(desc_w, g.baseline, s(f"budget.{key}"), align="R")
            pdf.line(ax, g.row(r + k + 1), ax + aw, g.row(r + k + 1))
