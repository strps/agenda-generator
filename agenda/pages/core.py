"""Core pages."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
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
