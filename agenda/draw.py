"""Drawing helpers on top of fpdf2 (lines, boxes, patterns)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from functools import lru_cache
from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import holidays_for, month_grid
from agenda.config import Config
from agenda.grid import Grid, Rect
from agenda.i18n import Strings

_INNER_FILL = (200, 220, 255)  # blue: inner (binding) margin
_OUTER_FILL = (255, 225, 190)  # orange: outer margin
_BOX = (120, 120, 120)
_COL_FILL = (255, 190, 215)
_BASELINE = (150, 200, 235)
_RULER = (90, 90, 90)


def _ruler_ticks(pdf: FPDF, length: float, vertical: bool) -> None:
    """Ticks every 1/5/10 mm along one page edge (top or left); labels every 10 mm."""
    pdf.set_draw_color(*_RULER)
    pdf.set_text_color(*_RULER)
    pdf.set_line_width(0.1)
    pdf.set_font("Inter", "", 4)
    for mm in range(int(length) + 1):
        size = 3.0 if mm % 10 == 0 else 2.0 if mm % 5 == 0 else 1.0
        if vertical:
            pdf.line(0, mm, size, mm)
        else:
            pdf.line(mm, 0, mm, size)
        if mm % 10 == 0 and mm:
            if vertical:
                pdf.text(3.4, mm + 0.5, str(mm))
            else:
                pdf.text(mm - 1.0, 5.2, str(mm))


def draw_debug_grid(pdf: FPDF, grid: Grid, page_no: int | None = None) -> None:
    """Overlay margins (inner blue / outer orange), header/content/footer boxes, columns,
    5 mm baseline rules and mm rulers on the current page. Restores graphics state."""
    w, h, s = grid.page_w, grid.page_h, grid.safe
    pdf.set_fill_color(*_INNER_FILL)
    pdf.set_draw_color(*_BOX)
    with pdf.local_context(fill_opacity=0.5, stroke_opacity=0.9):
        if grid.side == "left":
            inner_x, outer_x = w - grid.inner, 0
        else:
            inner_x, outer_x = 0, w - grid.outer
        pdf.set_fill_color(*_INNER_FILL)
        pdf.rect(inner_x, 0, grid.inner, h, style="F")
        pdf.set_fill_color(*_OUTER_FILL)
        pdf.rect(outer_x, 0, grid.outer, h, style="F")
        # top/bottom margin bands in the neutral tint
        pdf.set_fill_color(235, 235, 235)
        pdf.rect(s.x, 0, s.w, grid.top, style="F")
        pdf.rect(s.x, s.y2, s.w, grid.bottom, style="F")

        # columns with gutters
        pdf.set_fill_color(*_COL_FILL)
        with pdf.local_context(fill_opacity=0.25):
            for i in range(grid.columns):
                pdf.rect(grid.col_x(i), grid.content.y, grid.col_width, grid.content.h, style="F")

        # baseline rules every 5 mm over the content box
        pdf.set_draw_color(*_BASELINE)
        pdf.set_line_width(0.1)
        for n in range(grid.rows + 1):
            y = grid.row(n)
            pdf.line(s.x, y, s.x2, y)

        # safe area, header, content, footer outlines
        pdf.set_draw_color(*_BOX)
        pdf.set_line_width(0.2)
        pdf.rect(s.x, s.y, s.w, s.h)
        pdf.set_line_width(0.1)
        for r in (grid.header, grid.content, grid.footer):
            pdf.rect(*r)

    # rulers and label (opaque thin ink)
    pdf.set_line_width(0.1)
    _ruler_ticks(pdf, w, vertical=False)
    _ruler_ticks(pdf, h, vertical=True)
    pdf.set_text_color(*_RULER)
    pdf.set_font("Inter", "B", 6)
    label = f"{'p.' + str(page_no) + ' ' if page_no else ''}{grid.side} page  inner {grid.inner:g} / outer {grid.outer:g} mm"
    pdf.text(s.x + 6, s.y + 4, label)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(0, 0, 0)
    pdf.set_line_width(0.2)


def draw_mini_month(
    pdf: FPDF,
    rect: Rect,
    year: int,
    month: int,
    lang: str = "es",
    week_start: str = "monday",
    day_style: Callable[[date], DayStyle | None] | None = None,
    title_pt: float = tokens.TYPE_SIZES_PT[1],
    body_pt: float = tokens.TYPE_SIZES_PT[0],
) -> None:
    """Mini month calendar filling ``rect``: month name, weekday initials, then the day grid.

    The block is split into 8 equal lines (title, weekday row, 6 weeks) and 7 equal columns.
    ``day_style(date)`` is a hook returning ``DayStyle`` (text color, fill color; either may be
    None) or None for the default look; holiday/weekend marking plugs in here.
    """
    s = Strings(lang)
    line_h = rect.h / 8
    col_w = rect.w / 7
    pdf.c_margin = 0
    pdf.set_text_color(*tokens.COLORS["accent"])
    pdf.set_font("Inter", "B", title_pt)
    pdf.set_xy(rect.x, rect.y)
    pdf.cell(rect.w, line_h, s.month_name(month))
    pdf.set_text_color(*tokens.COLORS["muted"])
    pdf.set_font("Inter", "", body_pt)
    for i, name in enumerate(s.weekday_names(week_start, "letter")):
        pdf.set_xy(rect.x + i * col_w, rect.y + line_h)
        pdf.cell(col_w, line_h, name, align="C")
    for r, week in enumerate(month_grid(year, month, week_start)):
        y = rect.y + (2 + r) * line_h
        for i, d in enumerate(week):
            if d is None:
                continue
            style = day_style(d) if day_style else None
            x = rect.x + i * col_w
            if style and style.fill:
                pdf.set_fill_color(*style.fill)
                pdf.rect(x, y, col_w, line_h, style="F")
            pdf.set_text_color(*((style and style.color) or tokens.COLORS["ink"]))
            pdf.set_xy(x, y)
            pdf.cell(col_w, line_h, str(d.day), align="C")


class DayStyle(NamedTuple):
    color: tuple[int, int, int] | None = None
    fill: tuple[int, int, int] | None = None


WEEKEND_STYLE = DayStyle(color=tokens.COLORS["muted"], fill=tokens.COLORS["weekend_fill"])
HOLIDAY_STYLE = DayStyle(color=tokens.COLORS["accent"], fill=tokens.COLORS["holiday_fill"])


@lru_cache(maxsize=32)
def _holidays(year: int, country: str, language: str) -> dict[date, str]:
    return holidays_for(year, country, language)


def holiday_name_for(config: Config) -> Callable[[date], str | None]:
    """Return ``f(date) -> holiday name or None`` for ``config.holiday_country``/``language``.

    Holidays are cached per (year, country, language); unknown country raises ValueError.
    """

    def name(d: date) -> str | None:
        return _holidays(d.year, config.holiday_country, config.language).get(d)

    name(date(config.year, 1, 1))  # fail early on a bad country
    return name


def day_style_for(config: Config) -> Callable[[date], DayStyle | None]:
    """Return ``f(date) -> DayStyle | None`` marking holidays (strong) and Sat/Sun (light).

    Weekends are Saturday and Sunday regardless of ``config.week_start``; a holiday on a
    weekend gets the holiday style.
    """
    holiday = holiday_name_for(config)

    def style(d: date) -> DayStyle | None:
        if holiday(d):
            return HOLIDAY_STYLE
        if d.weekday() >= 5:
            return WEEKEND_STYLE
        return None

    return style


def draw_pattern(pdf: FPDF, rect: Rect, pattern: str, pitch: float) -> None:
    """Fill ``rect`` with a notes pattern anchored at its top-left on a ``pitch`` mm lattice.

    ``lined``: horizontal rules; ``dotted``: dots at lattice points; ``grid``: squares
    (rules both ways); ``blank`` (or anything else): nothing. Everything stays inside ``rect``.
    """
    if pattern not in ("lined", "dotted", "grid") or pitch <= 0:
        return
    cols = int(rect.w / pitch + 1e-6)
    rows = int(rect.h / pitch + 1e-6)
    pdf.set_draw_color(*tokens.COLORS["line"])
    pdf.set_line_width(tokens.STROKE_HAIRLINE)
    if pattern in ("lined", "grid"):
        for r in range(1 if pattern == "lined" else 0, rows + 1):
            y = rect.y + r * pitch
            pdf.line(rect.x, y, rect.x + (cols * pitch if pattern == "grid" else rect.w), y)
    if pattern == "grid":
        for c in range(cols + 1):
            x = rect.x + c * pitch
            pdf.line(x, rect.y, x, rect.y + rows * pitch)
    if pattern == "dotted":
        with pdf.local_context(stroke_cap_style="round", line_width=0.4):
            for r in range(rows + 1):
                for c in range(cols + 1):
                    x, y = rect.x + c * pitch, rect.y + r * pitch
                    pdf.line(x, y, x + 0.01, y)


def draw_checkbox(pdf: FPDF, x: float, y: float, size: float) -> None:
    """Empty square checkbox with top-left corner ``(x, y)`` and side ``size`` mm."""
    pdf.set_draw_color(*tokens.COLORS["muted"])
    pdf.set_line_width(tokens.STROKE_LIGHT)
    pdf.rect(x, y, size, size)


def draw_label_rule(pdf: FPDF, x: float, w: float, y: float, label: str, label_w: float) -> None:
    """Muted ``label`` ending on baseline ``y`` followed by a hairline rule to ``x + w``.

    The label cell sits one row above ``y`` (row height = text box); uses the current font.
    """
    pdf.set_text_color(*tokens.COLORS["muted"])
    pdf.set_xy(x, y - tokens.BASELINE)
    pdf.cell(label_w, tokens.BASELINE, label)
    pdf.set_draw_color(*tokens.COLORS["line"])
    pdf.set_line_width(tokens.STROKE_HAIRLINE)
    pdf.line(x + label_w, y, x + w, y)


def draw_circle(pdf: FPDF, cx: float, cy: float, d: float) -> None:
    """Empty circle centred on ``(cx, cy)`` with diameter ``d`` mm (light stroke, muted)."""
    pdf.set_draw_color(*tokens.COLORS["muted"])
    pdf.set_line_width(tokens.STROKE_LIGHT)
    pdf.ellipse(cx - d / 2, cy - d / 2, d, d, style="D")


MOOD_LEVELS = (1, 2, 3, 4, 5)
_MOOD_CURVE = {1: -0.24, 2: -0.1, 3: 0.0, 4: 0.1, 5: 0.24}  # mouth bend / d; + smiles


def draw_mood(pdf: FPDF, cx: float, cy: float, d: float, level: int) -> None:
    """Mood face centred on ``(cx, cy)``, diameter ``d`` mm: ``level`` 1 (very sad) to 5 (very happy).

    Drawn from an outline circle, two dot eyes and a mouth polyline whose bend goes from a deep
    frown (1) through a straight line (3) to a wide smile (5); level 1 adds slanted brows and
    level 5 closes the mouth with a chord. No glyphs.
    """
    if level not in _MOOD_CURVE:
        raise ValueError(f"mood level must be 1..5, got {level}")
    ink = tokens.COLORS["muted"]
    pdf.set_draw_color(*ink)
    pdf.set_fill_color(*ink)
    pdf.set_line_width(tokens.STROKE_LIGHT)
    pdf.ellipse(cx - d / 2, cy - d / 2, d, d, style="D")
    eye = d * 0.07
    for sx in (-1, 1):
        ex, ey = cx + sx * d * 0.18, cy - d * 0.12
        pdf.ellipse(ex - eye, ey - eye, 2 * eye, 2 * eye, style="F")
        if level == 1:  # worried brows, inner ends raised
            pdf.line(ex + sx * d * 0.1, ey - d * 0.12, ex - sx * d * 0.1, ey - d * 0.2)
    steps = 8
    curve = _MOOD_CURVE[level] * d
    y0 = cy + d * 0.22
    pts = []
    for i in range(steps + 1):
        u = 2 * i / steps - 1
        pts.append((cx + u * d * 0.24, y0 + curve * (1 - u * u)))
    if level == 3:
        pts = [pts[0], pts[-1]]
    pdf.polyline(pts, style="D")
    if level == 5:
        pdf.line(*pts[0], *pts[-1])
