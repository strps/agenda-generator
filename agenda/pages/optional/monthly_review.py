"""MonthlyReview page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, draw_checkbox, draw_circle, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


@register
class MonthlyReview(BasePage):
    """Monthly review, 1 page per month (12 instances): four write-in sections and a rating.

    Sections in order: wins, challenges, lessons, goals for next month (checkbox rows). Each is
    a label row, ``n`` write-in rules and a gap row; the last row holds the satisfaction label
    and ``RATING`` small circles (1 to 5) right-aligned, ``CIRCLE_PITCH`` baselines apart.
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (4 labels, 4 gaps, 1 rating row);
    the rest is split equally among the sections, leftover rows going to the first sections, so
    small pages get fewer rules instead of overflowing. Never negative.
    """

    id = "monthly_review"
    per_month = True
    name = "Monthly review"
    category = "optional"
    section = "optional"

    SECTIONS = ("wins", "challenges", "lessons", "goals")
    FIXED_ROWS = len(SECTIONS) * 2 + 1
    RATING = 5
    CIRCLE_RATIO = 0.7
    CIRCLE_PITCH = 2.0  # in baselines
    BOX_RATIO = 0.6  # checkbox side as a fraction of a baseline

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int, int, int]:
        """Write-in rows per section (wins, challenges, lessons, goals) for ``rows`` rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        n = len(cls.SECTIONS)
        base, extra = divmod(free, n)
        counts = [base + (i < extra) for i in range(n)]
        return counts[0], counts[1], counts[2], counts[3]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("review.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x, w = g.safe.x, g.safe.w
        box = g.baseline * self.BOX_RATIO
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        r = 0
        for key, n in zip(self.SECTIONS, self.layout(g.rows), strict=True):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(r))
            pdf.cell(w, g.baseline, s(f"review.{key}"))
            for k in range(n):
                y = g.row(r + 2 + k)
                if key == "goals":
                    draw_checkbox(pdf, x, y - g.baseline + (g.baseline - box) / 2, box)
                    pdf.line(x + box + g.gutter, y, x + w, y)
                else:
                    pdf.line(x, y, x + w, y)
            r += n + 2

        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(r))
        pdf.cell(w, g.baseline, s("review.rating"))
        pitch = g.baseline * self.CIRCLE_PITCH
        diam = g.baseline * self.CIRCLE_RATIO
        x0 = g.safe.x2 - self.RATING * pitch
        for i in range(self.RATING):
            draw_circle(pdf, x0 + (i + 0.5) * pitch, g.row(r) + g.baseline / 2, diam)
