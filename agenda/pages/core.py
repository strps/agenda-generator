"""Core pages."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import month_grid
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import DayStyle, draw_mini_month
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx

_INK = tokens.COLORS["ink"]
_ACCENT = tokens.COLORS["accent"]
_TINT = tokens.COLORS["tint"]


@register
class Cover(BasePage):
    """Front cover: accent block with the year and a localized title, inside the safe area."""

    id = "cover"
    name = "Cover"
    category = "core"
    section = "front_back"

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        c = g.content
        # Tinted panel over the top two thirds of the content rows, snapped to the baseline.
        panel = g.span(0, g.columns, 0, g.rows_in(c.h * 2 / 3))
        pdf.set_fill_color(*_TINT)
        pdf.rect(panel.x, panel.y, panel.w, panel.h, style="F")
        pdf.set_fill_color(*_ACCENT)
        pdf.rect(panel.x, panel.y, panel.w, tokens.SPACING[1], style="F")

        pdf.c_margin = 0
        # Title (18 pt) then year (28 pt), left-aligned on the panel's lower rows.
        title_y = g.row(g.rows_in(panel.h) - 8)
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
        pdf.set_xy(panel.x + tokens.SPACING[3], title_y)
        pdf.cell(panel.w - 2 * tokens.SPACING[3], 2 * g.baseline, s("cover.title"))
        pdf.set_text_color(*_INK)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[5])
        pdf.set_xy(panel.x + tokens.SPACING[3], title_y + 2 * g.baseline)
        pdf.cell(panel.w - 2 * tokens.SPACING[3], 3 * g.baseline, str(config.year))


@register
class PersonalInfo(BasePage):
    """Personal information: heading and labeled write-in lines on the baseline grid."""

    id = "personal_info"
    name = "Personal information"
    category = "core"
    section = "front_back"

    # (i18n key, rows available for writing)
    FIELDS = (
        ("personal.name", 1),
        ("personal.address", 2),
        ("personal.phone", 1),
        ("personal.email", 1),
        ("personal.emergency", 1),
        ("personal.blood_type", 1),
    )

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        x, w = g.col(0, g.columns)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
        pdf.set_xy(x, g.row(0))
        pdf.cell(w, 2 * g.baseline, s("personal.title"))

        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        row = 3
        for key, lines in self.FIELDS:
            if row + 1 + lines > g.rows:  # no room left: drop the remaining fields
                break
            pdf.set_text_color(*_INK)
            pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(row))
            pdf.cell(w, g.baseline, s(key))
            for i in range(lines):
                y = g.row(row + 2 + i)  # bottom edge of the write-in row
                pdf.line(x, y, x + w, y)
            row += 1 + lines + 2


@register
class Yearly(BasePage):
    """Yearly calendar on one page: 12 mini months in a 3 x 4 grid (2 grid columns each)."""

    id = "yearly"
    name = "Yearly calendar"
    category = "core"
    section = "front_back"

    MONTH_COLS = 3
    MONTH_ROWS = 4

    @staticmethod
    def day_style(d: date) -> DayStyle | None:
        """Hook for task 12 (weekend/holiday marking): return a ``DayStyle`` or None."""
        return

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, str(config.year))

        span = g.columns // self.MONTH_COLS
        per = g.rows // self.MONTH_ROWS  # baseline rows per block, one of them is the gap
        for m in range(1, 13):
            r, c = divmod(m - 1, self.MONTH_COLS)
            cell = g.span(c * span, span, r * per, per - 1)
            draw_mini_month(
                pdf, cell, config.year, m, config.language, config.week_start, self.day_style
            )


@register
class Monthly(BasePage):
    """Monthly planner on one page: month header, weekday row, day boxes, priorities block."""

    id = "monthly"
    name = "Monthly planner"
    category = "core"
    section = "monthly"

    @staticmethod
    def day_style(d: date) -> DayStyle | None:
        """Hook for task 12 (weekend/holiday marking): return a ``DayStyle`` or None."""
        return

    def instances(self, config: Config) -> list[Ctx]:
        return [{"month": m} for m in range(1, 13)]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        month = ctx["month"]
        x, w = g.col(0, g.columns)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("month.title", month=s.month_name(month), year=config.year))

        weeks = month_grid(config.year, month, config.week_start)
        notes_rows = max(4, g.rows // 5)  # priorities block: label + write-in lines
        grid_rows = g.rows - 1 - notes_rows - 1  # weekday row and a gap row excluded
        top = g.row(1)
        box_w = w / 7
        box_h = grid_rows * g.baseline / len(weeks)

        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        for i, name in enumerate(s.weekday_names(config.week_start, "short")):
            pdf.set_xy(x + i * box_w, g.row(0))
            pdf.cell(box_w, g.baseline, name, align="C")

        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        pad = tokens.SPACING[0]
        for r, week in enumerate(weeks):
            for i, d in enumerate(week):
                bx, by = x + i * box_w, top + r * box_h
                style = self.day_style(d) if d else None
                if style and style.fill:
                    pdf.set_fill_color(*style.fill)
                    pdf.rect(bx, by, box_w, box_h, style="DF")
                else:
                    pdf.rect(bx, by, box_w, box_h)
                if d is None:
                    continue
                pdf.set_text_color(*((style and style.color) or _INK))
                pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
                pdf.set_xy(bx + pad, by + pad)
                pdf.cell(box_w - 2 * pad, g.baseline, str(d.day))

        # Priorities: label then write-in lines at row bottoms.
        n0 = 1 + grid_rows + 1
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(n0))
        pdf.cell(w, g.baseline, s("priorities"))
        for n in range(n0 + 2, g.rows + 1):
            y = g.row(n)
            pdf.line(x, y, x + w, y)
