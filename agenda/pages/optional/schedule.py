"""Schedule page."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import weekday_order
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, font
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


@register
class Schedule(BasePage):
    """Weekly timetable, 1 page (classes / shifts): hour rows down the left, weekday columns.

    All 7 weekdays, ordered by ``config.week_start`` (short localized names): on b6 the day
    columns are still ~11 mm wide, enough for a 3-letter name and a short note, so no combined
    weekend column is needed. The hour label column is half a grid column; Saturday and Sunday
    get the ``weekend_fill`` tint. Row 0 holds the weekday names, then one band per hour from
    ``FIRST_HOUR``, each ``row_h`` baselines tall.
    Fit rule (``layout(rows)``): take the tallest hour band (``BAND_ROWS``, 3 > 2 > 1 baselines)
    that still shows at least ``MIN_HOURS`` hours; hours = ``(rows - 1) // row_h`` capped at
    ``MAX_HOURS`` (7:00-21:00). Small pages therefore get thinner bands, then fewer hours.
    """

    id = "schedule"
    name = "Weekly schedule"
    category = "optional"
    section = "optional"

    FIRST_HOUR = 7
    MAX_HOURS = 15
    MIN_HOURS = 10
    BAND_ROWS = (3, 2, 1)
    DAYS = 7

    @classmethod
    def layout(cls, rows: int, max_hours: int = MAX_HOURS) -> tuple[int, int]:
        """(hours, baselines per hour) for ``rows`` content rows (one is the weekday row)."""
        free = max(0, rows - 1)
        for rh in cls.BAND_ROWS:
            if free // rh >= cls.MIN_HOURS:
                return min(max_hours, free // rh), rh
        return min(max_hours, free), 1

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("schedule.title"))

        max_hours = config.schedule_last_hour - config.schedule_first_hour + 1
        hours, rh = self.layout(g.rows, max_hours)
        x = g.safe.x
        gx = x + g.col_width / 2
        day_w = (g.safe.x2 - gx) / self.DAYS
        bottom = g.row(1 + hours * rh)
        names = s.weekday_names(config.week_start, "short")
        order = weekday_order(config.week_start)

        pdf.set_fill_color(*color(pdf, "weekend_fill"))
        for i, wd in enumerate(order):
            if wd >= 5:
                pdf.rect(gx + i * day_w, g.row(1), day_w, bottom - g.row(1), style="F")

        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        for i, name in enumerate(names):
            pdf.set_xy(gx + i * day_w, g.row(0))
            pdf.cell(day_w, g.baseline, name, align="C")
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
        for k in range(hours):
            pdf.set_xy(x, g.row(1 + k * rh))
            pdf.cell(
                gx - x - g.gutter / 2, g.baseline, f"{config.schedule_first_hour + k}:00", align="R"
            )

        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(hours + 1):
            y = g.row(1 + k * rh)
            pdf.line(gx, y, g.safe.x2, y)
        for i in range(self.DAYS + 1):
            pdf.line(gx + i * day_w, g.row(1), gx + i * day_w, bottom)
