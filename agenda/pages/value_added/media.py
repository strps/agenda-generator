"""Media log page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_circle,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


class MediaLayout(NamedTuple):
    rows: int  # log rows that fit
    circle_d: float  # rating circle diameter, mm
    show_date: bool  # whether the "date finished" column is kept


@register
class Media(BasePage):
    """Books, movies and series log, ``count`` pages (default 1; id ``media_log``, value score 3).

    The catalog gives no repetition, so ``Media(count=N)`` gives N pages like Todo and Gratitude.
    A header row of small column labels, then log rows of ``ROW_ROWS`` baselines with a hairline
    rule under each. Columns, left to right: type (the three localized labels Book / Movie /
    Series stacked small, to circle one), title (takes the remaining width), date finished
    (``DATE_COLS`` grid columns) and a rating of ``RATING`` empty circles (``draw_circle``).

    Fit rule (``layout(...)``, all derived from the grid): rows = (content rows - 1 header row)
    // ``ROW_ROWS``, so small pages get fewer rows and nothing overflows. The columns need
    type + title minimum (``TITLE_COLS`` grid columns) + date + rating widths plus a gutter
    between columns. The circles are the limiting width: the diameter tries ``CIRCLE_RATIOS``
    (fractions of a baseline row, largest first) and the first that fits wins; only if even the
    smallest does not fit is the date column dropped (b6-class widths), and the circles are
    then re-sized with the freed width (largest ratio that fits). Circles sit ``CIRCLE_GAP`` of a diameter apart.
    """

    id = "media_log"
    added_value = 3
    name = "Books, movies and series"
    category = "value_added"
    section = "value_added"

    TYPES = ("book", "movie", "series")
    RATING = 5
    ROW_ROWS = 3
    DATE_COLS = 1
    TITLE_COLS = 2
    CIRCLE_RATIOS = (1.0, 0.8, 0.6)
    CIRCLE_GAP = 0.4

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def rating_width(cls, d: float) -> float:
        """Width of the 5-circle rating for circle diameter ``d``."""
        return cls.RATING * d + (cls.RATING - 1) * d * cls.CIRCLE_GAP

    @classmethod
    def layout(
        cls, rows: int, width: float, type_w: float, date_w: float, title_min: float, g: Grid
    ) -> MediaLayout:
        """Rows, circle size and date visibility for ``rows`` baselines and ``width`` mm.

        ``type_w``/``date_w``/``title_min`` are the type column, date column and the minimum
        title width in mm; ``g`` supplies baseline and gutter.
        """
        n = max(0, (rows - 1) // cls.ROW_ROWS)
        for show_date in (True, False):
            fixed = type_w + title_min + (date_w if show_date else 0)
            gaps = g.gutter * (3 if show_date else 2)
            for ratio in cls.CIRCLE_RATIOS:
                d = g.baseline * ratio
                if fixed + gaps + cls.rating_width(d) <= width:
                    return MediaLayout(n, d, show_date)
        return MediaLayout(n, g.baseline * cls.CIRCLE_RATIOS[-1], False)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("media.title"))

        x, w = g.safe.x, g.safe.w
        small = tokens.TYPE_SIZES_PT[0]
        pdf.set_font(font(pdf, "secondary"), "", small)
        type_w = max(pdf.get_string_width(s(f"media.{t}")) for t in self.TYPES) + g.gutter / 2
        date_w = g.span_width(self.DATE_COLS)
        lay = self.layout(g.rows, w, type_w, date_w, g.span_width(self.TITLE_COLS), g)

        rating_w = self.rating_width(lay.circle_d)
        rx = g.safe.x2 - rating_w
        dx = rx - g.gutter - date_w
        title_x = x + type_w + g.gutter
        title_end = (dx if lay.show_date else rx) - g.gutter
        row_h = g.baseline * self.ROW_ROWS

        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", small)
        for cx, cw, key in (
            (x, type_w, "media.type"),
            (title_x, title_end - title_x, "media.name"),
            (dx, date_w, "media.date"),
            (rx, rating_w, "media.rating"),
        ):
            if key == "media.date" and not lay.show_date:
                continue
            pdf.set_xy(cx, g.row(0))
            pdf.cell(cw, g.baseline, s(key))

        pdf.set_font(font(pdf, "secondary"), "", small)
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        line_h = row_h / len(self.TYPES)
        for r in range(lay.rows):
            top = g.row(1) + r * row_h
            pdf.set_text_color(*color(pdf, "muted"))
            for k, t in enumerate(self.TYPES):
                pdf.set_xy(x, top + k * line_h)
                pdf.cell(type_w, line_h, s(f"media.{t}"))
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            pdf.line(title_x, top + row_h, title_end, top + row_h)
            if lay.show_date:
                pdf.line(dx, top + row_h, dx + date_w, top + row_h)
            pitch = lay.circle_d * (1 + self.CIRCLE_GAP)
            for q in range(self.RATING):
                draw_circle(
                    pdf, rx + lay.circle_d / 2 + q * pitch, top + row_h - g.baseline, lay.circle_d
                )
