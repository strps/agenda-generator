"""QR codes page."""

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
from agenda.pages.value_added._common import _fit


class QRLayout(NamedTuple):
    cols: int
    rows: int
    cell_w: float  # width of one cell (QR + caption), mm
    cell_h: float
    side: float  # side of the square holding the QR with its quiet zone, mm

    @property
    def per_page(self) -> int:
        return self.cols * self.rows


@register
class QRCodes(BasePage):
    """QR codes for ``config.qr_urls`` (id ``qr``, value score 5).

    One page per ``per_page`` codes, ``ceil(len(urls) / per_page)`` pages; no URLs gives no
    instances (``build_plan`` just skips the page, it still builds). ctx = ``{"urls": [...]}``.

    Layout rule (``layout(w, h, baseline, gutter)``): 2 columns; 3 rows when the square left
    after a ``CAPTION_ROWS``-baseline caption is at least ``MIN_FILL`` of the cell width, else 2
    rows (today a5, b6 and letter all get 2x2). The QR square is the smaller of cell width
    and cell height minus caption. Under each code: the text (shortened with "..." to fit) and a
    write-in "Name" rule. Modules are filled vector rects with a ``QUIET`` module quiet zone;
    module size = side / (matrix size + 2 * QUIET).
    """

    id = "qr"
    added_value = 5
    name = "QR codes"
    category = "value_added"
    section = "value_added"

    COLS = 2
    CAPTION_ROWS = 2
    MIN_FILL = 0.8
    QUIET = 4

    def instances(self, config: Config) -> list[Ctx]:
        urls = config.qr_urls
        g = Grid.from_config(config)
        k = self.layout(g.content.w, g.content.h, g.baseline, g.gutter).per_page
        return [{"urls": urls[i : i + k]} for i in range(0, len(urls), k)]

    @classmethod
    def layout(cls, w: float, h: float, baseline: float, gutter: float) -> QRLayout:
        cell_w = (w - (cls.COLS - 1) * gutter) / cls.COLS
        caption = cls.CAPTION_ROWS * baseline
        rows = 2
        for r in (3, 2):
            rows = r
            if (h - (r - 1) * gutter) / r - caption >= cls.MIN_FILL * cell_w:
                break
        cell_h = (h - (rows - 1) * gutter) / rows
        return QRLayout(cls.COLS, rows, cell_w, cell_h, min(cell_w, cell_h - caption))

    @staticmethod
    def matrix(text: str) -> list[list[bool]]:
        """QR module matrix (True = dark) without quiet zone."""
        import qrcode

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
        qr.add_data(text)
        qr.make(fit=True)
        return qr.get_matrix()

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("qr.title"))

        c = g.content
        lay = self.layout(c.w, c.h, g.baseline, g.gutter)
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        label_w = pdf.get_string_width(s("qr.label")) + g.gutter
        for k, text in enumerate(ctx["urls"]):
            r, col = divmod(k, lay.cols)
            x = c.x + col * (lay.cell_w + g.gutter)
            y = c.y + r * (lay.cell_h + g.gutter)
            m = self.matrix(text)
            mod = lay.side / (len(m) + 2 * self.QUIET)
            x0 = x + (lay.cell_w - lay.side) / 2 + self.QUIET * mod
            y0 = y + self.QUIET * mod
            pdf.set_fill_color(0, 0, 0)
            for i, row in enumerate(m):
                for j, dark in enumerate(row):
                    if dark:
                        pdf.rect(x0 + j * mod, y0 + i * mod, mod, mod, style="F")
            cap = y + lay.side
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(x, cap)
            pdf.cell(lay.cell_w, g.baseline, _fit(pdf, text, lay.cell_w))
            draw_label_rule(pdf, x, lay.cell_w, cap + 2 * g.baseline, s("qr.label"), label_w)
