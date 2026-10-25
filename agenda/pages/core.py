"""Core pages."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_of_year, month_grid, weeks_by_month
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import DayStyle, day_style_for, draw_mini_month, draw_pattern, holiday_name_for
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx

_INK = tokens.COLORS["ink"]
_ACCENT = tokens.COLORS["accent"]
_TINT = tokens.COLORS["tint"]


def _cover_panel(pdf: FPDF, g: Grid, title: str, year: str) -> None:
    """Shared cover look: tinted panel with accent bar, title (18 pt) and year (28 pt)."""
    c = g.content
    # Tinted panel over the top two thirds of the content rows, snapped to the baseline.
    panel = g.span(0, g.columns, 0, g.rows_in(c.h * 2 / 3))
    pdf.set_fill_color(*_TINT)
    pdf.rect(panel.x, panel.y, panel.w, panel.h, style="F")
    pdf.set_fill_color(*_ACCENT)
    pdf.rect(panel.x, panel.y, panel.w, tokens.SPACING[1], style="F")

    pdf.c_margin = 0
    title_y = g.row(g.rows_in(panel.h) - 8)
    pdf.set_text_color(*_ACCENT)
    pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
    pdf.set_xy(panel.x + tokens.SPACING[3], title_y)
    pdf.cell(panel.w - 2 * tokens.SPACING[3], 2 * g.baseline, title)
    pdf.set_text_color(*_INK)
    pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[5])
    pdf.set_xy(panel.x + tokens.SPACING[3], title_y + 2 * g.baseline)
    pdf.cell(panel.w - 2 * tokens.SPACING[3], 3 * g.baseline, year)


@register
class Cover(BasePage):
    """Front cover: accent block with the year and a localized title, inside the safe area."""

    id = "cover"
    name = "Cover"
    category = "core"
    section = "front_back"

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        s = Strings(config.language)
        _cover_panel(pdf, grids[0], s("cover.title"), str(config.year))


@register
class BackCover(BasePage):
    """Back cover: same panel as ``Cover`` with a short localized line and the year."""

    id = "back_cover"
    name = "Back cover"
    category = "core"
    section = "front_back"

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        s = Strings(config.language)
        _cover_panel(pdf, grids[0], s("back_cover.line"), str(config.year))


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

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[4])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, str(config.year))

        day_style = day_style_for(config)
        span = g.columns // self.MONTH_COLS
        per = g.rows // self.MONTH_ROWS  # baseline rows per block, one of them is the gap
        for m in range(1, 13):
            r, c = divmod(m - 1, self.MONTH_COLS)
            cell = g.span(c * span, span, r * per, per - 1)
            draw_mini_month(
                pdf, cell, config.year, m, config.language, config.week_start, day_style
            )


@register
class Monthly(BasePage):
    """Monthly planner on one page: month header, weekday row, day boxes, priorities block."""

    id = "monthly"
    name = "Monthly planner"
    category = "core"
    section = "monthly"

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

        day_style = day_style_for(config)
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
                style = day_style(d) if d else None
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


@register
class Weekly(BasePage):
    """Weekly planner, a WO2P spread: 4 days on the left page, 3 days + notes on the right.

    ctx keys: ``number`` (ISO week), ``iso_year``, ``days`` (7 dates in ``week_start`` order,
    may belong to adjacent years) and ``month`` (owning month 1..12, see ``weeks_by_month``).
    """

    id = "weekly"
    name = "Weekly planner"
    category = "core"
    section = "weekly"
    pages = 2
    starts_on = "left"

    LEFT_DAYS = 4  # blocks per page; right page shows the remaining days plus a notes block
    BLOCKS = 4

    def instances(self, config: Config) -> list[Ctx]:
        by_month = weeks_by_month(config.year, config.week_start)
        return [
            {"number": w.number, "iso_year": w.iso_year, "days": list(w.days), "month": m}
            for m, weeks in by_month.items()
            for w in weeks
        ]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        s = Strings(config.language)
        days: list[date] = ctx["days"]
        style_of, name_of = day_style_for(config), holiday_name_for(config)
        last = pdf.page
        pdf.page = last - 1  # left page
        self._page(
            pdf,
            grids[0],
            s,
            days[: self.LEFT_DAYS],
            s("week.number", n=ctx["number"]),
            style_of,
            name_of,
        )
        pdf.page = last
        months = []
        for d in days:
            name = s.month_name(d.month)
            label = f"{name} {d.year}" if d.year != days[0].year else name
            if label not in months:
                months.append(label)
        title = " – ".join(months)
        if days[0].year == days[-1].year:
            title += f" {days[0].year}"
        self._page(pdf, grids[1], s, days[self.LEFT_DAYS :], title, style_of, name_of, notes=True)

    def _page(
        self,
        pdf: FPDF,
        g: Grid,
        s: Strings,
        days: list[date],
        title: str,
        style_of: Callable[[date], DayStyle | None],
        name_of: Callable[[date], str | None],
        notes: bool = False,
    ) -> None:
        x, w = g.col(0, g.columns)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, title)

        per = g.rows // self.BLOCKS  # rows per block: label row + write-in lines
        pad = tokens.SPACING[0]
        names = s.weekday_names("monday", "full")
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for i in range(self.BLOCKS):
            r0 = i * per
            y0 = g.row(r0)
            if i < len(days):
                d = days[i]
                style = style_of(d)
                if style and style.fill:
                    pdf.set_fill_color(*style.fill)
                    pdf.rect(x, y0, w, g.baseline, style="F")
                pdf.set_text_color(*((style and style.color) or _INK))
                pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
                pdf.set_xy(x + pad, y0)
                label = f"{names[d.weekday()]} {d.day}"
                pdf.cell(w - 2 * pad, g.baseline, label)
                holiday = name_of(d)
                if holiday:  # right-aligned, only if it fits next to the day label
                    pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
                    hw = pdf.get_string_width(holiday)
                    pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
                    if hw + pdf.get_string_width(label) + 2 * pad < w - 2 * pad:
                        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
                        pdf.set_xy(x + pad, y0)
                        pdf.cell(w - 2 * pad, g.baseline, holiday, align="R")
            elif notes:
                pdf.set_text_color(*_ACCENT)
                pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
                pdf.set_xy(x + pad, y0)
                pdf.cell(w - 2 * pad, g.baseline, s("notes.title"))
            else:
                continue
            pdf.line(x, y0, x + w, y0)  # block top rule
            for n in range(r0 + 2, r0 + per + 1):
                y = g.row(n)
                pdf.line(x, y, x + w, y)


@register
class Daily(BasePage):
    """Daily planner, 1 page: date header, hourly schedule (left) and priorities/notes (right).

    ctx keys: ``date``, ``week`` (ISO week number), ``iso_year``. One ctx per day of
    ``config.year``; ``daily_months`` is not applied here (Phase 4).
    Schedule hours: ``HOUR_START``..``HOUR_END`` (06:00-21:00), fewer if rows run short.
    """

    id = "daily"
    name = "Daily planner"
    category = "core"
    section = "daily"

    HOUR_START = 6
    HOUR_END = 21

    def instances(self, config: Config) -> list[Ctx]:
        out = []
        for d in days_of_year(config.year):
            iso = d.isocalendar()
            out.append({"date": d, "week": iso.week, "iso_year": iso.year})
        return out

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        d: date = ctx["date"]
        pdf.c_margin = 0
        h = g.header
        style = day_style_for(config)(d)
        if style and style.fill:
            pdf.set_fill_color(*style.fill)
            pdf.rect(h.x, h.y, h.w, h.h, style="F")
        pdf.set_text_color(*((style and style.color) or _ACCENT))
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        title = s(
            "day.title",
            weekday=s.weekday_names("monday", "full")[d.weekday()],
            day=d.day,
            month=s.month_name(d.month),
        )
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, title)
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("week.number", n=ctx["week"]), align="R")

        gap = 1
        sched_cols = (g.columns + 1) // 2
        sx, sw = g.col(0, sched_cols - gap if g.columns > 2 else sched_cols)
        rx, rw = g.col(sched_cols, g.columns - sched_cols) if g.columns > 2 else (sx, sw)
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)

        # Hourly schedule: label row, then one block of `per` rows per hour.
        self._label(pdf, g, s("schedule"), sx, sw, 0)
        n_hours = min(self.HOUR_END - self.HOUR_START + 1, g.rows - 1)
        per = (g.rows - 1) // n_hours
        label_w = 8.0
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        for i in range(n_hours):
            r0 = 1 + i * per
            pdf.set_xy(sx, g.row(r0))
            pdf.cell(label_w, g.baseline, f"{self.HOUR_START + i:02d}:00")
            y = g.row(r0 + per)
            pdf.line(sx, y, sx + sw, y)

        # Right column: priorities (top half) and notes (bottom half) with write-in lines.
        half = g.rows // 2
        for title_key, r0, r1 in (("priorities", 0, half), ("notes.title", half, g.rows)):
            self._label(pdf, g, s(title_key), rx, rw, r0)
            for n in range(r0 + 2, r1 + 1):
                y = g.row(n)
                pdf.line(rx, y, rx + rw, y)

    @staticmethod
    def _label(pdf: FPDF, g: Grid, text: str, x: float, w: float, row: int) -> None:
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(row))
        pdf.cell(w, g.baseline, text)


@register
class Notes(BasePage):
    """Notes, 1 page: localized header and a pattern (``config.notes_pattern``) over the content.

    The pattern is anchored to the content box on the baseline pitch, so it lines up with the
    baseline grid. ``Notes(count=N)`` makes ``instances()`` return N pages (default 1); Phase 4
    padding uses this. ``blank`` draws only the header.
    """

    id = "notes"
    name = "Notes"
    category = "core"
    section = "front_back"

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("notes.title"))
        draw_pattern(pdf, g.content, config.notes_pattern, g.baseline)


@register
class Contacts(BasePage):
    """Contact directory, 1 page: header and entries (name, phone, email write-in rows).

    Entries fill the content box top to bottom, in 2 columns when the page is wide enough.
    ``Contacts(count=N)`` makes ``instances()`` return N pages (default 1), like ``Notes``.
    """

    id = "contacts"
    name = "Contacts"
    category = "core"
    section = "front_back"

    FIELDS = ("contacts.name", "contacts.phone", "contacts.email")
    ENTRY_ROWS = len(FIELDS) + 1  # one spacing row after each entry
    WIDE_MM = 100.0  # safe width from which entries go in 2 columns
    LABEL_W = 14.0

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("contacts.title"))

        ncols = 2 if g.safe.w >= self.WIDE_MM and g.columns >= 2 else 1
        span = g.columns // ncols
        per_col = g.rows // self.ENTRY_ROWS
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        for c in range(ncols):
            x, w = g.col(c * span, span if c < ncols - 1 else g.columns - c * span)
            if c < ncols - 1:  # keep a column gap
                w = g.col(c * span, span - 1)[1] if span > 1 else w
            for e in range(per_col):
                for i, key in enumerate(self.FIELDS):
                    r = e * self.ENTRY_ROWS + i
                    pdf.set_text_color(*tokens.COLORS["muted"])
                    pdf.set_xy(x, g.row(r))
                    pdf.cell(self.LABEL_W, g.baseline, s(key))
                    y = g.row(r + 1)
                    pdf.line(x + self.LABEL_W, y, x + w, y)
