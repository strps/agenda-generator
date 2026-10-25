"""Value-added pages."""

from __future__ import annotations

import math
from datetime import date
from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_in_month
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import MOOD_LEVELS, draw_checkbox, draw_circle, draw_label_rule, draw_mood
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


class MealsLayout(NamedTuple):
    day_rows: int  # baselines per weekday row of the planner
    grocery_rows: int  # grocery rows per column
    grocery_cols: int  # 1 or 2


@register
class Meals(BasePage):
    """Meal and grocery planner, 1 page (value score 4; the catalog gives no repetition).

    Top: the weekly planner. A label row (breakfast / lunch / dinner), then 7 weekday rows in
    ``config.week_start`` order (short localized names in a ``NAME_COLS``-wide column, the three
    meal cells share the rest, hairline-framed). Below: a gap row, a "Groceries" label row and
    checkbox + item rules, in ``GROCERY_COLS`` columns when the page has at least
    ``TWO_COL_ROWS`` rows, else one column.

    Fit rule (``layout(rows)``): the planner gets ``PLANNER_SHARE`` of the rows, spent as 1
    label row plus 7 days of ``day_rows`` baselines (1..``MAX_DAY_ROWS``). Groceries get what is
    left after the gap and label rows, so small pages get fewer grocery rows, never overflow.
    """

    id = "meals"
    name = "Meal and grocery planner"
    category = "value_added"
    section = "value_added"

    MEALS = ("breakfast", "lunch", "dinner")
    DAYS = 7
    PLANNER_SHARE = 0.6
    MAX_DAY_ROWS = 4
    NAME_COLS = 1
    TWO_COL_ROWS = 30
    BOX = 3.0

    @classmethod
    def layout(cls, rows: int) -> MealsLayout:
        """Planner day height and grocery rows per column for ``rows`` baseline rows."""
        day_rows = max(1, min(cls.MAX_DAY_ROWS, (int(rows * cls.PLANNER_SHARE) - 1) // cls.DAYS))
        rest = max(0, rows - (1 + cls.DAYS * day_rows) - 2)
        return MealsLayout(day_rows, rest, 2 if rows >= cls.TWO_COL_ROWS else 1)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("meals.title"))

        day_rows, per_col, ncols = self.layout(g.rows)
        x = g.safe.x
        gx = x + g.span_width(self.NAME_COLS) + g.gutter
        cell_w = (g.safe.x2 - gx) / len(self.MEALS)
        row_h = day_rows * g.baseline

        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        for i, key in enumerate(self.MEALS):
            pdf.set_xy(gx + i * cell_w, g.row(0))
            pdf.cell(cell_w, g.baseline, s(f"meals.{key}"), align="C")
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for d, name in enumerate(s.weekday_names(config.week_start, "short")):
            y = g.row(1) + d * row_h
            pdf.set_xy(x, y)
            pdf.cell(gx - x - g.gutter, row_h, name)
            for i in range(len(self.MEALS)):
                pdf.rect(gx + i * cell_w, y, cell_w, row_h)

        top = 1 + self.DAYS * day_rows + 1
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(top))
        pdf.cell(g.safe.w, g.baseline, s("meals.groceries"))
        box = min(self.BOX, g.baseline - 1.0)
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for c in range(ncols):
            cx, cw = g.col(c * (g.columns // ncols), g.columns // ncols)
            for k in range(per_col):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                draw_checkbox(pdf, cx, ty + (g.baseline - box) / 2, box)
                pdf.line(cx + box + 2, y, cx + cw, y)


class GratitudeLayout(NamedTuple):
    lines: int  # write-in rows per block (grateful, best moment)
    last_lines: int  # write-in rows of the final "intention" block (takes the remainder)


@register
class Gratitude(BasePage):
    """Gratitude journal, ``count`` pages (default 1; value score 4, the catalog gives no repetition).

    Header: title plus a "Date" write-in field on the first content row. Then ``GRATEFUL_BLOCKS``
    numbered "I am grateful for..." blocks (label row + numbered write-in rules, the number drawn
    as small muted text in a one-baseline column), a "Best moment of the day" block and a final
    "Intention for tomorrow" block, all with plain rules. Blocks are separated by one empty row.

    Fit rule (``layout(rows)``): fixed rows = date row + one label row per block + one gap row
    between blocks; the rest is split evenly in ``lines`` write-in rows per block (at least 1,
    so b6 gets 3 and letter more), and the remainder goes to the final block. Numbering
    continues across a block's rows. ``Gratitude(count=N)`` gives N pages; there is no config
    field for the count yet, like Todo.
    """

    id = "gratitude"
    name = "Gratitude journal"
    category = "value_added"
    section = "value_added"

    GRATEFUL_BLOCKS = 3
    BLOCKS = GRATEFUL_BLOCKS + 2
    DATE_COLS = 2

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> GratitudeLayout:
        """Write-in rows per block and for the last block, for ``rows`` baseline rows."""
        fixed = 1 + cls.BLOCKS + (cls.BLOCKS - 1)
        lines = max(1, (rows - fixed) // cls.BLOCKS)
        return GratitudeLayout(lines, max(1, rows - fixed - lines * (cls.BLOCKS - 1)))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("gratitude.title"))

        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        label = s("gratitude.date")
        dx, dw = g.col(g.columns - self.DATE_COLS, self.DATE_COLS)
        draw_label_rule(pdf, dx, dw, g.row(1), label, pdf.get_string_width(label) + g.gutter)

        lines, last = self.layout(g.rows)
        x, num_w = g.safe.x, g.baseline
        top = 1
        for b in range(self.BLOCKS):
            n = last if b == self.BLOCKS - 1 else lines
            key = (
                "gratitude.grateful"
                if b < self.GRATEFUL_BLOCKS
                else ("gratitude.best" if b == self.GRATEFUL_BLOCKS else "gratitude.intention")
            )
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(x, g.row(top))
            pdf.cell(g.safe.w, g.baseline, s(key))
            pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            for k in range(n):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                if b < self.GRATEFUL_BLOCKS:
                    pdf.set_text_color(*tokens.COLORS["muted"])
                    pdf.set_xy(x, ty)
                    pdf.cell(num_w, g.baseline, str(k + 1))
                pdf.line(x + num_w, y, g.safe.x2, y)
            top += 1 + n + 1


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
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("media.title"))

        x, w = g.safe.x, g.safe.w
        small = tokens.TYPE_SIZES_PT[0]
        pdf.set_font("Inter", "", small)
        type_w = max(pdf.get_string_width(s(f"media.{t}")) for t in self.TYPES) + g.gutter / 2
        date_w = g.span_width(self.DATE_COLS)
        lay = self.layout(g.rows, w, type_w, date_w, g.span_width(self.TITLE_COLS), g)

        rating_w = self.rating_width(lay.circle_d)
        rx = g.safe.x2 - rating_w
        dx = rx - g.gutter - date_w
        title_x = x + type_w + g.gutter
        title_end = (dx if lay.show_date else rx) - g.gutter
        row_h = g.baseline * self.ROW_ROWS

        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", small)
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

        pdf.set_font("Inter", "", small)
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        line_h = row_h / len(self.TYPES)
        for r in range(lay.rows):
            top = g.row(1) + r * row_h
            pdf.set_text_color(*tokens.COLORS["muted"])
            for k, t in enumerate(self.TYPES):
                pdf.set_xy(x, top + k * line_h)
                pdf.cell(type_w, line_h, s(f"media.{t}"))
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            pdf.line(title_x, top + row_h, title_end, top + row_h)
            if lay.show_date:
                pdf.line(dx, top + row_h, dx + date_w, top + row_h)
            pitch = lay.circle_d * (1 + self.CIRCLE_GAP)
            for q in range(self.RATING):
                draw_circle(
                    pdf, rx + lay.circle_d / 2 + q * pitch, top + row_h - g.baseline, lay.circle_d
                )


class TravelLayout(NamedTuple):
    day_rows: int  # itinerary day rows
    pack_rows: int  # packing rows per column
    pack_cols: int  # packing columns (1 or 2)


@register
class Travel(BasePage):
    """Travel planner, ``count`` pages (default 1; id ``travel``, value score 4).

    The catalog gives no repetition, so ``Travel(count=N)`` gives N pages like Todo and Media.
    Top to bottom: destination row, from | to dates row, budget row (``FIELD_ROWS``, label +
    rule), a gap, the itinerary (label row + day rows, each a short "Day N" column and a rule),
    a gap and the packing list (label row + checkbox + rule rows).

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (fields, 2 gaps, 2 labels); the
    remaining rows are split by ``ITINERARY_SHARE`` (rounded down) for the itinerary and the
    rest for packing. Packing uses two columns when the page has at least ``TWO_COL_ROWS`` rows
    (a5, letter), one on shorter pages (b6); smaller pages just get fewer rows, never overflow.
    """

    id = "travel"
    name = "Travel planner"
    category = "value_added"
    section = "value_added"

    FIELD_ROWS = 3
    FIXED_ROWS = FIELD_ROWS + 4  # fields, gap, itinerary label, gap, packing label
    ITINERARY_SHARE = 0.6
    TWO_COL_ROWS = 30
    BOX_RATIO = 0.7  # checkbox side as a fraction of a baseline row
    MAX_DAYS = 14

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> TravelLayout:
        """Itinerary day rows and packing rows/columns for ``rows`` baseline rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        days = min(cls.MAX_DAYS, int(free * cls.ITINERARY_SHARE))
        return TravelLayout(
            days, free - int(free * cls.ITINERARY_SHARE), 2 if rows >= cls.TWO_COL_ROWS else 1
        )

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("travel.title"))

        x, w = g.safe.x, g.safe.w
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        keys = ("destination", "from", "to", "budget")
        label_w = max(pdf.get_string_width(s(f"travel.{k}")) for k in keys) + g.gutter
        draw_label_rule(pdf, x, w, g.row(1), s("travel.destination"), label_w)
        span = g.columns // 2
        lx, lw = g.col(0, span)
        rx, rw = g.col(span, g.columns - span)
        draw_label_rule(pdf, lx, lw, g.row(2), s("travel.from"), label_w)
        draw_label_rule(pdf, rx, rw, g.row(2), s("travel.to"), label_w)
        draw_label_rule(pdf, x, w, g.row(3), s("travel.budget"), label_w)

        days, pack, ncols = self.layout(g.rows)
        top = self.FIELD_ROWS + 1
        small = tokens.TYPE_SIZES_PT[0]
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", small)
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("travel.itinerary"))
        pdf.set_font("Inter", "", small)
        day_w = pdf.get_string_width(f"{s('travel.day')} {self.MAX_DAYS}") + g.gutter
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(days):
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_xy(x, g.row(top + 1 + k))
            pdf.cell(day_w, g.baseline, f"{s('travel.day')} {k + 1}")
            y = g.row(top + 2 + k)
            pdf.line(x + day_w, y, x + w, y)

        top += days + 2
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", small)
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("travel.packing"))
        box = g.baseline * self.BOX_RATIO
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for c in range(ncols):
            cx, cw = g.col(c * (g.columns // ncols), g.columns // ncols)
            for k in range(pack):
                ty, y = g.row(top + 1 + k), g.row(top + 2 + k)
                draw_checkbox(pdf, cx, ty + (g.baseline - box) / 2, box)
                pdf.line(cx + box + g.gutter / 2, y, cx + cw, y)


class ChallengeLayout(NamedTuple):
    cols: int  # day cell columns
    grid_rows: int  # day cell rows (cols * grid_rows >= DAYS)
    cell_rows: int  # baselines per day cell
    reflect_rows: int  # write-in rules under the "Reflection" label


@register
class Challenge30(BasePage):
    """30-day challenge, ``count`` pages (default 1; id ``challenges30``, value score 4).

    The catalog gives no repetition, so ``Challenge30(count=N)`` gives N pages like Todo and
    Travel. Top to bottom: "My challenge" and "Why" label + rule rows, a gap, exactly 30 day
    cells (small day number in the top-left corner, a circle to tick), a gap and a
    "Reflection" label with write-in rules over the remaining rows.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (2 fields, 2 gaps, the label);
    the grid must leave ``MIN_REFLECT_ROWS`` rules. Grid shapes are ``COLS`` (5 x 6 or 6 x 5;
    both tile 30 exactly). The tallest ``cell_rows`` (``MAX_CELL_ROWS`` down to
    ``MIN_CELL_ROWS`` baselines) that fits wins, ties go to fewer columns (wider cells).
    Cells are as wide as the safe width allows (gutter between cells), so b6 keeps six
    ~15 mm cells. Rows left over become reflection rules.
    """

    id = "challenges30"
    name = "30-day challenges"
    category = "value_added"
    section = "value_added"

    DAYS = 30
    COLS = (5, 6)
    FIELD_ROWS = 2
    FIXED_ROWS = FIELD_ROWS + 3  # fields, gap, gap, reflection label
    MIN_REFLECT_ROWS = 2
    MIN_CELL_ROWS = 2
    MAX_CELL_ROWS = 4
    CIRCLE_RATIO = 0.8  # tick circle diameter as a fraction of a baseline

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> ChallengeLayout:
        """Grid shape and reflection rules for ``rows`` baseline rows."""
        avail = rows - cls.FIXED_ROWS - cls.MIN_REFLECT_ROWS
        for cell_rows in range(cls.MAX_CELL_ROWS, cls.MIN_CELL_ROWS - 1, -1):
            for cols in cls.COLS:
                nrows = -(-cls.DAYS // cols)
                if nrows * cell_rows <= avail:
                    free = rows - cls.FIXED_ROWS - nrows * cell_rows
                    return ChallengeLayout(cols, nrows, cell_rows, free)
        cols = cls.COLS[-1]
        return ChallengeLayout(cols, -(-cls.DAYS // cols), cls.MIN_CELL_ROWS, 0)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("challenge.title"))

        x, w = g.safe.x, g.safe.w
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        label_w = (
            max(pdf.get_string_width(s(k)) for k in ("challenge.mine", "challenge.why")) + g.gutter
        )
        draw_label_rule(pdf, x, w, g.row(1), s("challenge.mine"), label_w)
        draw_label_rule(pdf, x, w, g.row(2), s("challenge.why"), label_w)

        lay = self.layout(g.rows)
        top = self.FIELD_ROWS + 1
        cw = (w - (lay.cols - 1) * g.gutter) / lay.cols
        ch = lay.cell_rows * g.baseline
        d = g.baseline * self.CIRCLE_RATIO
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
        for k in range(self.DAYS):
            r, c = divmod(k, lay.cols)
            cx = x + c * (cw + g.gutter)
            cy = g.row(top + 1) + r * ch
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            pdf.rect(cx, cy, cw, ch)
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_xy(cx + g.gutter / 3, cy)
            pdf.cell(cw / 2, g.baseline, str(k + 1))
            draw_circle(pdf, cx + cw / 2, cy + (ch + g.baseline) / 2, d)

        top += 1 + lay.grid_rows * lay.cell_rows + 1
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(top))
        pdf.cell(w, g.baseline, s("challenge.reflection"))
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(lay.reflect_rows):
            y = g.row(top + 2 + k)
            pdf.line(x, y, x + w, y)


class IdeaLayout(NamedTuple):
    centre: tuple[float, float]  # centre of the main shape, relative to the area's top-left
    centre_radii: tuple[float, float]  # (rx, ry) of the main ellipse
    sat_radii: tuple[float, float]  # (rx, ry) of every satellite ellipse
    satellites: list[tuple[float, float]]  # satellite centres, same origin, clockwise from top


@register
class IdeaMap(BasePage):
    """Idea map (mind map), ``count`` pages (default 1; id ``ideas``, value score 3).

    The catalog gives no repetition, so ``IdeaMap(count=N)`` gives N pages like Todo and Travel.
    Header with the title, then a canvas filling the content box: a central ellipse labelled
    "Main idea" with a write-in rule, and satellite ellipses, each joined to the centre by a
    line and holding a short write-in rule.

    Layout rule (``layout(w, h)``, all ratios of the canvas ``w`` x ``h``, no millimetres):
    satellites sit on an ellipse of radii ``ORBIT`` (fractions of w and h) around the centre,
    evenly spaced by angle, the first at the top and then clockwise. The count is
    ``MAX_SATELLITES`` (8) when ``w >= WIDE_RATIO * h`` (letter), else ``MIN_SATELLITES`` (6)
    (a5, b6), so narrow canvases keep roomier shapes. Shape radii are fractions of w and h
    chosen so no bounding boxes overlap and everything stays inside the canvas.
    """

    id = "ideas"
    name = "Idea map"
    category = "value_added"
    section = "value_added"

    MIN_SATELLITES = 6
    MAX_SATELLITES = 8
    WIDE_RATIO = 0.78
    CENTRE_RADII = (0.16, 0.10)  # fractions of (w, h)
    SAT_RADII = (0.16, 0.06)
    ORBIT = (0.33, 0.43)
    RULE_Y = 0.3  # satellite rule offset below its centre, fraction of ry
    RULE_W = 0.7  # rule half-width as a fraction of rx

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, w: float, h: float) -> IdeaLayout:
        """Shapes for a ``w`` x ``h`` canvas, positions relative to its top-left."""
        n = cls.MAX_SATELLITES if w >= cls.WIDE_RATIO * h else cls.MIN_SATELLITES
        cx, cy = w / 2, h / 2
        sats = []
        for k in range(n):
            t = -math.pi / 2 + 2 * math.pi * k / n
            sats.append((cx + cls.ORBIT[0] * w * math.cos(t), cy + cls.ORBIT[1] * h * math.sin(t)))
        return IdeaLayout(
            (cx, cy),
            (cls.CENTRE_RADII[0] * w, cls.CENTRE_RADII[1] * h),
            (cls.SAT_RADII[0] * w, cls.SAT_RADII[1] * h),
            sats,
        )

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("ideas.title"))

        c = g.content
        lay = self.layout(c.w, c.h)
        ox, oy = c.x, c.y
        cx, cy = ox + lay.centre[0], oy + lay.centre[1]
        crx, cry = lay.centre_radii
        srx, sry = lay.sat_radii

        pdf.set_draw_color(*tokens.COLORS["muted"])
        pdf.set_line_width(tokens.STROKE_LIGHT)
        for sx, sy in lay.satellites:
            pdf.line(cx, cy, ox + sx, oy + sy)
        pdf.set_fill_color(*tokens.COLORS["tint"])
        pdf.ellipse(cx - crx, cy - cry, 2 * crx, 2 * cry, style="DF")
        pdf.set_fill_color(255, 255, 255)
        for sx, sy in lay.satellites:
            pdf.ellipse(ox + sx - srx, oy + sy - sry, 2 * srx, 2 * sry, style="DF")

        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for sx, sy in lay.satellites:
            y = oy + sy + sry * self.RULE_Y
            pdf.line(ox + sx - srx * self.RULE_W, y, ox + sx + srx * self.RULE_W, y)
        y = cy + cry * self.RULE_Y
        pdf.line(cx - crx * self.RULE_W, y, cx + crx * self.RULE_W, y)
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(cx - crx, cy - g.baseline)
        pdf.cell(2 * crx, g.baseline, s("ideas.main"), align="C")


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
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("qr.title"))

        c = g.content
        lay = self.layout(c.w, c.h, g.baseline, g.gutter)
        pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
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
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(x, cap)
            pdf.cell(lay.cell_w, g.baseline, _fit(pdf, text, lay.cell_w))
            draw_label_rule(pdf, x, lay.cell_w, cap + 2 * g.baseline, s("qr.label"), label_w)


def _fit(pdf: FPDF, text: str, width: float) -> str:
    """``text`` shortened with "..." so it fits ``width`` mm in the current font."""
    if pdf.get_string_width(text) <= width:
        return text
    while text and pdf.get_string_width(text + "...") > width:
        text = text[:-1]
    return text + "..."


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
        pdf.set_draw_color(*tokens.COLORS["muted"])
        pdf.set_fill_color(*tokens.COLORS["tint"])
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
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
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
            pdf.set_text_color(*_ACCENT)
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(g.safe.x, y)
            pdf.cell(num_w, g.baseline, str(k + 1))
            self._icon(pdf, key, g.safe.x + num_w, y, icon)
            pdf.set_text_color(*tokens.COLORS["ink"])
            pdf.set_xy(text_x, y)
            pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[0])
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
            pdf.set_text_color(*tokens.COLORS["muted"])
            pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(g.safe.x, g.row(top))
            pdf.cell(g.safe.w, g.baseline, s("extras.supplies"))
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            box = g.baseline * 0.6
            for k in range(lay.supply_rows):
                y = g.row(top + 1 + k)
                draw_checkbox(pdf, g.safe.x, y - box - (g.baseline - box) / 2, box)
                pdf.set_draw_color(*tokens.COLORS["line"])
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.line(g.safe.x + g.baseline, y, g.safe.x2, y)


class _Counted(BasePage):
    """Shared ``count=N`` behaviour of the niche pack pages (default 1, negatives raise)."""

    category = "value_added"
    section = "value_added"

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @staticmethod
    def _header(pdf: FPDF, g: Grid, title: str) -> None:
        pdf.c_margin = 0
        pdf.set_text_color(*_ACCENT)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[3])
        pdf.set_xy(g.header.x, g.header.y)
        pdf.cell(g.header.w, g.header.h, title)

    @staticmethod
    def _label(pdf: FPDF, g: Grid, x: float, w: float, row: int, text: str) -> None:
        """Small bold muted label whose text cell starts at ``g.row(row)``."""
        pdf.set_text_color(*tokens.COLORS["muted"])
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(row))
        pdf.cell(w, g.baseline, text)

    @staticmethod
    def _rules(pdf: FPDF, g: Grid, x: float, w: float, first: int, n: int) -> None:
        """``n`` hairline write-in rules on lines ``first`` .. ``first + n - 1``."""
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(n):
            pdf.line(x, g.row(first + k), x + w, g.row(first + k))


class EntrepreneurLayout(NamedTuple):
    metric_rows: int  # height of each big metric write-in box, in baselines
    pipeline_rows: int  # rule rows under the pipeline column headings
    decision_rows: int  # rule rows under "Decisions & lessons"


@register
class PackEntrepreneur(_Counted):
    """Entrepreneur weekly dashboard, ``count`` pages (default 1; id ``niche_entrepreneur``).

    The catalog lists the niche pages as ``niche_*`` (value score 5), so the three packs are
    ``niche_entrepreneur``, ``niche_student`` and ``niche_fitness``. Top to bottom: goal of the
    week (label + rule), 3 key metrics (label + big write-in box each, 2 columns wide), the
    pipeline (leads / in progress / closed, one column of rules each) and decisions & lessons.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (goal, metric label, pipeline
    title + headings, decisions label, 3 gaps); the free rows give the metric boxes
    ``free // METRIC_DIV`` rows clamped to 1..``METRIC_MAX``, the rest is split
    ``PIPELINE_SHARE`` (rounded down) to the pipeline and the remainder to decisions.
    """

    id = "niche_entrepreneur"
    name = "Entrepreneur pack"
    FIXED_ROWS = 9
    METRIC_DIV = 6
    METRIC_MAX = 4
    PIPELINE_SHARE = 0.6
    STAGES = ("leads", "progress", "closed")

    @classmethod
    def layout(cls, rows: int) -> EntrepreneurLayout:
        free = max(0, rows - cls.FIXED_ROWS)
        metric = max(1, min(cls.METRIC_MAX, free // cls.METRIC_DIV))
        rest = max(0, free - metric)
        pipe = int(rest * cls.PIPELINE_SHARE)
        return EntrepreneurLayout(metric, pipe, rest - pipe)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("entre.title"))
        x, w = g.safe.x, g.safe.w
        metric, pipe, dec = self.layout(g.rows)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        goal = s("entre.goal")
        draw_label_rule(pdf, x, w, g.row(1), goal, pdf.get_string_width(goal) + g.gutter)

        row = 3
        span = g.columns // 3
        for i in range(3):
            cx, cw = g.col(i * span, span)
            self._label(pdf, g, cx, cw, row, f"{s('entre.metric')} {i + 1}")
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_LIGHT)
            pdf.rect(
                cx, g.row(row + 1) + g.baseline * 0.2, cw - g.gutter, (metric - 0.4) * g.baseline
            )
        row += metric + 2

        self._label(pdf, g, x, w, row, s("entre.pipeline"))
        for i, key in enumerate(self.STAGES):
            cx, cw = g.col(i * span, span)
            self._label(pdf, g, cx, cw, row + 1, s(f"entre.{key}"))
            self._rules(pdf, g, cx, cw - g.gutter, row + 3, max(0, pipe - 1))
        row += pipe + 3

        self._label(pdf, g, x, w, row, s("entre.decisions"))
        self._rules(pdf, g, x, w, row + 2, max(0, dec - 1))


class StudentLayout(NamedTuple):
    table_rows: int  # course rows in the tracker table
    study: bool  # whether the study-hours block fits


@register
class PackStudent(_Counted):
    """Student course/exam tracker, ``count`` pages (default 1; id ``niche_student``).

    A heading row (course | exam or assignment | date | grade / weight) and course rows of
    ``ROW_BASELINES`` baselines filling the page, then a study-hours block (title, 7 weekday
    labels and 7 write-in boxes of ``STUDY_BOX_ROWS`` rows).

    Fit rule (``layout(rows)``): the study block takes ``STUDY_ROWS`` plus a gap; the table gets
    the rest after its heading row, in whole ``ROW_BASELINES`` rows. Pages too short for the
    block (rows < ``STUDY_ROWS + 5``) drop it and use all rows for the table.
    """

    id = "niche_student"
    name = "Student pack"
    ROW_BASELINES = 2
    STUDY_BOX_ROWS = 2
    STUDY_ROWS = STUDY_BOX_ROWS + 2  # title, weekday labels, boxes
    COLS = ((0, 2, "course"), (2, 2, "exam"), (4, 1, "date"), (5, 1, "grade"))
    DAYS = 7

    @classmethod
    def layout(cls, rows: int) -> StudentLayout:
        study = rows >= cls.STUDY_ROWS + 5
        free = rows - 1 - (cls.STUDY_ROWS + 1 if study else 0)
        return StudentLayout(max(0, free // cls.ROW_BASELINES), study)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("student.title"))
        x, w = g.safe.x, g.safe.w
        table, study = self.layout(g.rows)
        for col, span, key in self.COLS:
            cx, cw = g.col(col, span)
            self._label(pdf, g, cx, cw, 0, s(f"student.{key}"))
        for k in range(table):
            self._rules(pdf, g, x, w, 1 + (k + 1) * self.ROW_BASELINES - 1, 1)
        if not study:
            return
        top = 1 + table * self.ROW_BASELINES + 1
        self._label(pdf, g, x, w, top, s("student.study"))
        gap = g.gutter / 2
        bw = (w - gap * (self.DAYS - 1)) / self.DAYS
        pdf.set_draw_color(*tokens.COLORS["line"])
        pdf.set_line_width(tokens.STROKE_LIGHT)
        days = s.weekday_names(config.week_start, "short")
        for d in range(self.DAYS):
            bx = x + d * (bw + gap)
            self._label(pdf, g, bx, bw, top + 1, days[d])
            pdf.set_draw_color(*tokens.COLORS["line"])
            pdf.set_line_width(tokens.STROKE_LIGHT)
            pdf.rect(bx, g.row(top + 2), bw, self.STUDY_BOX_ROWS * g.baseline)


class FitnessLayout(NamedTuple):
    exercise_rows: int  # exercise rows in the log
    notes_rows: int  # rule rows under "Notes"


@register
class PackFitness(_Counted):
    """Fitness workout log, ``count`` pages (default 1; id ``niche_fitness``).

    Date row, then a heading row (exercise | sets | reps | weight) and exercise rows of
    ``ROW_BASELINES`` baselines. Columns come from the grid: exercise = 2 columns, sets = 2
    columns holding ``SET_CELLS`` small rects, reps and weight = 1 column each (a rule).
    Notes (label + rules) close the page.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` (date, heading, gap, notes label) are structure;
    notes get ``NOTES_SHARE`` of the free rows (at least ``NOTES_MIN``) and the exercise log
    takes the rest in whole ``ROW_BASELINES`` rows.
    """

    id = "niche_fitness"
    name = "Fitness pack"
    FIXED_ROWS = 4
    ROW_BASELINES = 2
    NOTES_SHARE = 0.2
    NOTES_MIN = 2
    SET_CELLS = 4
    CELL_RATIO = 1.2  # set rect height / baseline
    COLS = ((0, 2, "exercise"), (2, 2, "sets"), (4, 1, "reps"), (5, 1, "weight"))

    @classmethod
    def layout(cls, rows: int) -> FitnessLayout:
        free = max(0, rows - cls.FIXED_ROWS)
        notes = min(free, max(cls.NOTES_MIN, int(free * cls.NOTES_SHARE)))
        return FitnessLayout((free - notes) // cls.ROW_BASELINES, notes)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("fitness.title"))
        x, w = g.safe.x, g.safe.w
        ex, notes = self.layout(g.rows)
        pdf.set_font("Inter", "B", tokens.TYPE_SIZES_PT[1])
        date = s("fitness.date")
        draw_label_rule(pdf, x, w, g.row(1), date, pdf.get_string_width(date) + g.gutter)
        for col, span, key in self.COLS:
            cx, cw = g.col(col, span)
            self._label(pdf, g, cx, cw, 2, s(f"fitness.{key}"))
        sx, sw = g.col(2, 2)
        gap = g.gutter / 2
        cell = (sw - g.gutter - gap * (self.SET_CELLS - 1)) / self.SET_CELLS
        for k in range(ex):
            bottom = 3 + (k + 1) * self.ROW_BASELINES - 1
            self._rules(pdf, g, x, w, bottom, 1)
            pdf.set_draw_color(*tokens.COLORS["muted"])
            pdf.set_line_width(tokens.STROKE_LIGHT)
            for c in range(self.SET_CELLS):
                pdf.rect(
                    sx + c * (cell + gap),
                    g.row(bottom) - g.baseline * self.CELL_RATIO - g.baseline * 0.1,
                    cell,
                    g.baseline * self.CELL_RATIO,
                )
        top = 3 + ex * self.ROW_BASELINES + 1
        self._label(pdf, g, x, w, top, s("fitness.notes"))
        self._rules(pdf, g, x, w, top + 2, max(0, notes - 1))
