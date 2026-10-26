"""Vision board page."""

from __future__ import annotations

from typing import NamedTuple

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
from agenda.pages.base import BasePage, Ctx


class VisionLayout(NamedTuple):
    """Row/column plan of the vision board (all counts in baseline rows / cells)."""

    word_rows: int
    cols: int
    nrows: int
    cell_rows: int


@register
class VisionBoard(BasePage):
    """Free-form vision board, 1 page (value score 4).

    Header with the title, a "My vision for <year>" line, a "word of the year" box (label plus
    a write-in rule) and a framed grid of empty cells to paste photos or quotes; each cell has a
    caption rule below its frame. Drawn shapes only.

    Layout rule (``layout``, derived from the safe area, in baseline rows): the top block is
    ``INTRO_ROWS`` (vision line) + ``WORD_ROWS`` (word box) + ``GAP_ROWS``; the rest is the grid.
    Columns: 3 when the safe width is at least ``3 * MIN_CELL_W`` baselines, else 2. Grid rows:
    as many as fit at ``MIN_CELL_ROWS`` baselines per cell (frame + caption), at least 1, at
    most ``MAX_GRID_ROWS``; the cells then share the height evenly, ``GAP_ROWS`` between them.
    The caption occupies the last ``CAPTION_ROWS`` rows of each cell.
    """

    id = "vision_board"
    added_value = 4
    name = "Vision board"
    category = "value_added"
    section = "value_added"

    INTRO_ROWS = 2
    WORD_ROWS = 4
    GAP_ROWS = 1
    CAPTION_ROWS = 2
    MIN_CELL_W = 12
    MIN_CELL_ROWS = 8
    MAX_GRID_ROWS = 4

    @classmethod
    def layout(cls, rows: int, width_rows: float) -> VisionLayout:
        """Plan for ``rows`` content rows and a safe width of ``width_rows`` baselines."""
        top = cls.INTRO_ROWS + cls.WORD_ROWS + cls.GAP_ROWS
        avail = max(0, rows - top)
        cols = 3 if width_rows >= 3 * cls.MIN_CELL_W else 2
        nrows = min(
            cls.MAX_GRID_ROWS, max(1, (avail + cls.GAP_ROWS) // (cls.MIN_CELL_ROWS + cls.GAP_ROWS))
        )
        cell = max(0, (avail + cls.GAP_ROWS) // nrows - cls.GAP_ROWS)
        return VisionLayout(cls.WORD_ROWS, cols, nrows, cell)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("vision.title"))

        x, w = g.safe.x, g.safe.w
        lay = self.layout(g.rows, w / g.baseline)
        pdf.set_text_color(*color(pdf, "ink"))
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[2])
        pdf.set_xy(x, g.row(0))
        pdf.cell(w, g.baseline * self.INTRO_ROWS, s("vision.subtitle", year=config.year))

        # word of the year: framed box with a label and a write-in rule
        wy = g.row(self.INTRO_ROWS)
        wh = g.baseline * lay.word_rows
        pdf.set_draw_color(*color(pdf, "accent"))
        pdf.set_line_width(tokens.STROKE_REGULAR)
        pdf.rect(x, wy, w, wh)
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x + tokens.GUTTER, wy)
        pdf.cell(w - 2 * tokens.GUTTER, g.baseline * 2, s("vision.word"))
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        ry = wy + wh - g.baseline
        pdf.line(x + tokens.GUTTER, ry, x + w - tokens.GUTTER, ry)

        # grid of empty frames, each with a caption rule
        top = self.INTRO_ROWS + self.WORD_ROWS + self.GAP_ROWS
        cw = (w - (lay.cols - 1) * tokens.GUTTER) / lay.cols
        for r in range(lay.nrows):
            y0 = g.row(top + r * (lay.cell_rows + self.GAP_ROWS))
            fh = g.baseline * (lay.cell_rows - self.CAPTION_ROWS)
            for c in range(lay.cols):
                cx = x + c * (cw + tokens.GUTTER)
                pdf.set_draw_color(*color(pdf, "accent"))
                pdf.set_line_width(tokens.STROKE_LIGHT)
                pdf.rect(cx, y0, cw, fh)
                pdf.set_draw_color(*color(pdf, "line"))
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                cy = y0 + g.baseline * (lay.cell_rows - 1)
                pdf.line(cx, cy, cx + cw, cy)
