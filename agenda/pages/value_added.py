"""Value-added pages."""

from __future__ import annotations

from datetime import date
from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_in_month
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import MOOD_LEVELS, draw_checkbox, draw_circle, draw_mood
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs

_ACCENT = tokens.COLORS["accent"]


@register
class MonthlyQuotes(BasePage):
    """Motivational quote per month, 1 page per month (12 instances, value score 3).

    A large quote area (``QUOTE_SHARE`` of the content rows), then a label row and write-in
    rules for the user's own reflection. The quote for month ``m`` is i18n key ``quotes.<m>``.

    Quote rule: the built-in quotes are short original sayings written for this project and
    carry no attribution. A real author is named only for a genuinely public-domain quote that
    is certain; there are none today. Add new ones as ``quotes.<n>`` keys in every language.

    Fit rule: the quote is set in the largest of ``QUOTE_SIZES`` (indices into
    ``tokens.TYPE_SIZES_PT``) whose wrapped text fits the quote area at ``LINE_ROWS`` baselines
    per line; if none fits, the smallest is used and extra lines are dropped.
    """

    id = "quotes"
    name = "Monthly quotes"
    category = "value_added"
    section = "value_added"

    QUOTE_SHARE = 0.5
    QUOTE_SIZES = (4, 3, 2)
    LINE_ROWS = 2
    MIN_RULES = 1

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(quote area rows, reflection write-in rules) for ``rows`` baseline rows."""
        q = int(rows * cls.QUOTE_SHARE) // cls.LINE_ROWS * cls.LINE_ROWS
        return q, max(0, rows - q - 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("quotes.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x, w = g.safe.x, g.safe.w
        q_rows, rules = self.layout(g.rows)
        line_h = g.baseline * self.LINE_ROWS
        max_lines = max(1, q_rows // self.LINE_ROWS)
        text = s(f"quotes.{ctx['month']}")
        size = self.QUOTE_SIZES[-1]
        for size in self.QUOTE_SIZES:
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[size])
            lines = pdf.multi_cell(w, line_h, text, dry_run=True, output="LINES")
            if len(lines) <= max_lines:
                break
        lines = lines[:max_lines]
        pdf.set_text_color(*tokens.COLORS["ink"])
        y0 = g.row(0) + (q_rows - len(lines) * self.LINE_ROWS) / 2 * g.baseline
        for i, line in enumerate(lines):
            pdf.set_xy(x, y0 + i * line_h)
            pdf.cell(w, line_h, line)

        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(q_rows))
        pdf.cell(w, g.baseline, s("quotes.reflection"))
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(rules):
            y = g.row(q_rows + 2 + k)
            pdf.line(x, y, x + w, y)


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
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("vision.title"))

        x, w = g.safe.x, g.safe.w
        lay = self.layout(g.rows, w / g.baseline)
        pdf.set_text_color(*tokens.COLORS["ink"])
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[2])
        pdf.set_xy(x, g.row(0))
        pdf.cell(w, g.baseline * self.INTRO_ROWS, s("vision.subtitle", year=config.year))

        # word of the year: framed box with a label and a write-in rule
        wy = g.row(self.INTRO_ROWS)
        wh = g.baseline * lay.word_rows
        pdf.set_draw_color(*_ACCENT)
        pdf.set_line_width(tokens.STROKE_REGULAR)
        pdf.rect(x, wy, w, wh)
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x + tokens.GUTTER, wy)
        pdf.cell(w - 2 * tokens.GUTTER, g.baseline * 2, s("vision.word"))
        pdf.set_draw_color(*tokens.COLORS["line"])
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
                pdf.set_draw_color(*_ACCENT)
                pdf.set_line_width(tokens.STROKE_LIGHT)
                pdf.rect(cx, y0, cw, fh)
                pdf.set_draw_color(*tokens.COLORS["line"])
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                cy = y0 + g.baseline * (lay.cell_rows - 1)
                pdf.line(cx, cy, cx + cw, cy)


@register
class HealthTracker(BasePage):
    """Monthly health tracker, 1 page per month (12 instances, value score 4).

    Row 0-1: the mood legend, the 5 drawn faces (``draw_mood`` levels 1 very sad to 5 very
    happy) each with its level number, after a "Mood" label. Row ``LEGEND_ROWS + GAP_ROWS``
    holds the day numbers; below it, one tracker row of ``ROW_ROWS`` baselines per entry of
    ``TRACKERS`` (mood, water, sleep, exercise, other). The label column is the first
    ``NAME_COLS`` grid columns; the days of *that* month (28-31) share the rest equally, one
    hairline-framed cell per day per row. Cell content: mood a circle to mark or number, water
    ``GLASSES`` stacked small circles, sleep an empty cell for the hours, exercise a checkbox,
    other an empty cell. Weekend columns get the ``weekend_fill`` tint.

    Fit rule (``layout(rows)``): the cells are never shrunk below ``ROW_ROWS`` baselines
    high; instead trackers are dropped from the end of ``TRACKERS`` when the page is short
    (b6 keeps all of them at 2 baselines per row). Never negative.
    """

    id = "health"
    name = "Health tracker"
    category = "value_added"
    section = "value_added"

    TRACKERS = ("mood", "water", "sleep", "exercise", "other")
    LEGEND_ROWS = 2
    GAP_ROWS = 1
    DAYS_ROWS = 1
    ROW_ROWS = 2
    NAME_COLS = 2
    GLASSES = 4
    FACE_RATIO = 0.8  # legend face diameter as a fraction of LEGEND_ROWS baselines
    MARK_RATIO = 0.7  # in-cell mark size as a fraction of the smaller of cell width and height

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> int:
        """Number of tracker rows (leading entries of ``TRACKERS``) that fit in ``rows``."""
        free = rows - cls.LEGEND_ROWS - cls.GAP_ROWS - cls.DAYS_ROWS
        return max(0, min(len(cls.TRACKERS), free // cls.ROW_ROWS))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        month, year = ctx["month"], ctx["year"]
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("health.title", month=s.month_name(month), year=year))

        x = g.safe.x
        days = days_in_month(year, month)
        n = self.layout(g.rows)
        name_w = g.span_width(self.NAME_COLS)
        gx = x + name_w + g.gutter
        cell_w = (g.safe.x2 - gx) / days
        row_h = g.baseline * self.ROW_ROWS

        # mood legend: label, then the five faces with their level numbers
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        ly = g.row(0)
        pdf.set_xy(x, ly)
        pdf.cell(name_w, g.baseline * self.LEGEND_ROWS, s("health.mood"))
        face = g.baseline * self.LEGEND_ROWS * self.FACE_RATIO
        slot = (g.safe.x2 - gx) / len(MOOD_LEVELS)
        for i, level in enumerate(MOOD_LEVELS):
            fx = gx + i * slot
            draw_mood(pdf, fx + face / 2, ly + g.baseline * self.LEGEND_ROWS / 2, face, level)
            pdf.set_xy(fx + face + g.gutter / 2, ly)
            pdf.cell(slot - face, g.baseline * self.LEGEND_ROWS, str(level))

        top = g.row(self.LEGEND_ROWS + self.GAP_ROWS)
        grid_h = self.DAYS_ROWS * g.baseline + n * row_h
        pdf.set_fill_color(*tokens.COLORS["weekend_fill"])
        for d in range(days):
            if date(year, month, d + 1).weekday() >= 5:
                pdf.rect(gx + d * cell_w, top, cell_w, grid_h, style="F")
            pdf.set_xy(gx + d * cell_w, top)
            pdf.cell(cell_w, g.baseline, str(d + 1), align="C")

        mark = min(cell_w, row_h) * self.MARK_RATIO
        for k, key in enumerate(self.TRACKERS[:n]):
            y = top + g.baseline * self.DAYS_ROWS + k * row_h
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_xy(x, y)
            pdf.cell(name_w, row_h, s(f"health.{key}"))
            for d in range(days):
                cx = gx + (d + 0.5) * cell_w
                pdf.set_draw_color(*tokens.COLORS["line"])
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.rect(gx + d * cell_w, y, cell_w, row_h)
                if key == "mood":
                    draw_circle(pdf, cx, y + row_h / 2, mark)
                elif key == "water":
                    pitch = row_h / self.GLASSES
                    for q in range(self.GLASSES):
                        draw_circle(pdf, cx, y + (q + 0.5) * pitch, min(mark, pitch * 0.7))
                elif key == "exercise":
                    draw_checkbox(pdf, cx - mark / 2, y + (row_h - mark) / 2, mark)
