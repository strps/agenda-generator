"""Physical extras guide page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_checkbox,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx
from agenda.pages.value_added._common import _fit


class ExtrasLayout(NamedTuple):
    tips: int  # numbered tips shown
    supply_rows: int  # write-in rows of "my supplies" (0 = block dropped)


@register
class ExtrasGuide(BasePage):
    """Physical extras guide, 1 page (catalog id ``physical_extras``, value score 5).

    A fixed guide, so no ``count``. Header with the title, then numbered tips (folding and
    binding, stickers and washi tape, month tabs, ribbon marker, pen loop, pocket), each with a
    small icon drawn from rects, circles and lines plus up to two wrapped lines of text.

    Layout rule (``layout(rows)``): every tip takes ``TIP_ROWS`` baseline rows (2 text/icon rows
    and 1 gap). Tips are shown in order, ``min(len(TIPS), rows // TIP_ROWS)``, so short pages
    (b6) drop the last tips rather than overflow. Rows left after the tips, if at least
    ``SUPPLY_MIN_ROWS`` (label + 1 rule), hold the "My supplies" checklist, at most
    ``SUPPLY_MAX_ROWS`` checkbox rules.
    """

    id = "physical_extras"
    added_value = 5
    name = "Physical extras guide"
    category = "value_added"
    section = "value_added"

    TIPS = ("fold", "stickers", "tabs", "ribbon", "loop", "pocket")
    TIP_ROWS = 3
    ICON_ROWS = 2
    SUPPLY_MIN_ROWS = 2
    SUPPLY_MAX_ROWS = 4
    TEXT_LINES = 2

    def instances(self, config: Config) -> list[Ctx]:
        return [{}]

    @classmethod
    def layout(cls, rows: int) -> ExtrasLayout:
        """Tips shown and supply rule rows for ``rows`` baseline rows."""
        tips = max(0, min(len(cls.TIPS), rows // cls.TIP_ROWS))
        left = rows - tips * cls.TIP_ROWS
        if left < cls.SUPPLY_MIN_ROWS:
            return ExtrasLayout(tips, 0)
        return ExtrasLayout(tips, min(cls.SUPPLY_MAX_ROWS, left - 1))

    @staticmethod
    def _icon(pdf: FPDF, kind: str, x: float, y: float, d: float) -> None:
        """Icon for tip ``kind`` inside the ``d`` x ``d`` square at ``(x, y)``."""
        pdf.set_draw_color(*color(pdf, "muted"))
        pdf.set_fill_color(*color(pdf, "tint"))
        pdf.set_line_width(tokens.STROKE_LIGHT)
        if kind == "fold":  # sheet with a folded corner and a stitched spine
            pdf.rect(x + d * 0.15, y, d * 0.7, d, style="D")
            pdf.line(x + d * 0.55, y, x + d * 0.85, y + d * 0.3)
            pdf.line(x + d * 0.55, y, x + d * 0.55, y + d * 0.3)
            pdf.line(x + d * 0.55, y + d * 0.3, x + d * 0.85, y + d * 0.3)
            pdf.line(x + d * 0.3, y + d * 0.4, x + d * 0.3, y + d * 0.9)
        elif kind == "stickers":  # round sticker and a washi strip
            pdf.ellipse(x, y, d * 0.55, d * 0.55, style="DF")
            pdf.rect(x + d * 0.2, y + d * 0.65, d * 0.8, d * 0.3, style="DF")
            pdf.line(x + d * 0.4, y + d * 0.65, x + d * 0.4, y + d * 0.95)
        elif kind == "tabs":  # page edge with tabs
            pdf.rect(x, y, d * 0.75, d, style="D")
            for k in range(3):
                pdf.rect(x + d * 0.75, y + d * (0.05 + 0.32 * k), d * 0.25, d * 0.24, style="DF")
        elif kind == "ribbon":  # ribbon hanging from the spine with a notched end
            pdf.line(x + d * 0.3, y, x + d * 0.3, y + d)
            pdf.rect(x + d * 0.5, y, d * 0.2, d * 0.85, style="DF")
            pdf.line(x + d * 0.5, y + d, x + d * 0.6, y + d * 0.8)
            pdf.line(x + d * 0.7, y + d, x + d * 0.6, y + d * 0.8)
        elif kind == "loop":  # pen in a loop on the edge
            pdf.rect(x + d * 0.05, y + d * 0.1, d * 0.3, d * 0.8, style="D")
            pdf.rect(x + d * 0.4, y + d * 0.35, d * 0.55, d * 0.3, style="DF")
            pdf.line(x + d * 0.95, y + d * 0.5, x + d, y + d * 0.5)
        else:  # pocket: a card with a pocket flap
            pdf.rect(x, y, d, d, style="D")
            pdf.rect(x, y + d * 0.45, d, d * 0.55, style="DF")
            pdf.line(x, y + d * 0.45, x + d / 2, y + d * 0.7)
            pdf.line(x + d, y + d * 0.45, x + d / 2, y + d * 0.7)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("extras.title"))

        lay = self.layout(g.rows)
        icon = self.ICON_ROWS * g.baseline
        num_w = g.baseline
        text_x = g.safe.x + num_w + icon + g.gutter
        text_w = g.safe.x2 - text_x
        for k, key in enumerate(self.TIPS[: lay.tips]):
            top = 1 + k * self.TIP_ROWS
            y = g.row(top)
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(g.safe.x, y)
            pdf.cell(num_w, g.baseline, str(k + 1))
            self._icon(pdf, key, g.safe.x + num_w, y, icon)
            pdf.set_text_color(*color(pdf, "ink"))
            pdf.set_xy(text_x, y)
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
            lines = pdf.multi_cell(
                text_w, g.baseline, s(f"extras.{key}"), dry_run=True, output="LINES"
            )
            for i, line in enumerate(lines[: self.TEXT_LINES]):
                if i == self.TEXT_LINES - 1 and len(lines) > self.TEXT_LINES:
                    line = _fit(pdf, line + "...", text_w)
                pdf.set_xy(text_x, g.row(top + i))
                pdf.cell(text_w, g.baseline, line)

        if lay.supply_rows:
            top = 1 + lay.tips * self.TIP_ROWS
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(g.safe.x, g.row(top))
            pdf.cell(g.safe.w, g.baseline, s("extras.supplies"))
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            box = g.baseline * 0.6
            for k in range(lay.supply_rows):
                y = g.row(top + 1 + k)
                draw_checkbox(pdf, g.safe.x, y - box - (g.baseline - box) / 2, box)
                pdf.set_draw_color(*color(pdf, "line"))
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.line(g.safe.x + g.baseline, y, g.safe.x2, y)
