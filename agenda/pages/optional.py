"""Optional pages."""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

from agenda import tokens
from agenda.calendar import days_in_month, weekday_order
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import color, draw_checkbox, draw_circle, draw_label_rule, font, merged_holidays
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx, month_ctxs


def _draw_task_list(
    pdf: FPDF, g: Grid, row: int, n: int, labels: tuple[str, str], box: float, due_cols: int
) -> None:
    """Label row at baseline row ``row``, then ``n`` rows of checkbox + task rule + due rule.

    The due column is the last ``due_cols`` grid columns; the task rule ends one gutter before.
    """
    x = g.safe.x
    dx, dw = g.col(g.columns - due_cols, due_cols)
    task_w = dx - g.gutter - x
    box = min(box, g.baseline - 1.0)
    pdf.set_text_color(*color(pdf, "muted"))
    pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
    pdf.set_xy(x, g.row(row))
    pdf.cell(task_w, g.baseline, labels[0])
    pdf.set_xy(dx, g.row(row))
    pdf.cell(dw, g.baseline, labels[1])
    pdf.set_draw_color(*color(pdf, "line"))
    pdf.set_line_width(tokens.STROKE_HAIRLINE)
    for k in range(n):
        top, y = g.row(row + 1 + k), g.row(row + 2 + k)
        draw_checkbox(pdf, x, top + (g.baseline - box) / 2, box)
        pdf.line(x + box + 2, y, x + task_w, y)
        pdf.line(dx, y, dx + dw, y)


@register
class Goals(BasePage):
    """Yearly goals, 1 page: per goal a title rule, checkbox steps and a deadline rule.

    Fit rule (``layout(rows)``): a block is title + steps + deadline + 1 gap row. Try 6 goals,
    then 5, with the most steps (at most ``MAX_STEPS``) that fit; accept the first count that
    leaves at least ``MIN_STEPS`` steps. Small pages therefore get fewer steps, then 5 goals.
    """

    id = "goals"
    name = "Yearly goals"
    category = "optional"
    section = "optional"

    MAX_STEPS = 4
    MIN_STEPS = 2
    GOAL_COUNTS = (6, 5)
    LABEL_W = 22.0
    BOX = 3.0

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(goals, steps per goal) for ``rows`` baseline rows of content."""
        for n in cls.GOAL_COUNTS:
            steps = min(cls.MAX_STEPS, rows // n - 3)
            if steps >= cls.MIN_STEPS:
                return n, steps
        n = cls.GOAL_COUNTS[-1]
        return n, max(0, min(cls.MAX_STEPS, rows // n - 3))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("goals.title"))

        goals, steps = self.layout(g.rows)
        block = steps + 3
        x, w = g.safe.x, g.safe.w
        box = min(self.BOX, g.baseline - 1.0)
        for i in range(goals):
            r = i * block
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            draw_label_rule(pdf, x, w, g.row(r + 1), s("goals.goal", n=i + 1), self.LABEL_W)
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0])
            for k in range(steps):
                top, y = g.row(r + 1 + k), g.row(r + 2 + k)
                draw_checkbox(pdf, x, top + (g.baseline - box) / 2, box)
                pdf.set_draw_color(*color(pdf, "line"))
                pdf.set_line_width(tokens.STROKE_HAIRLINE)
                pdf.line(x + box + 2, y, x + w, y)
            draw_label_rule(pdf, x, w, g.row(r + 2 + steps), s("goals.deadline"), self.LABEL_W)


@register
class ImportantDates(BasePage):
    """Birthdays and anniversaries, 1 page: 12 month blocks in 2 columns x 6 rows.

    Fit rule (``layout(rows)``): each of the 6 block rows gets ``rows // 6`` baseline rows;
    one is the month title and one is the gap, the rest are write-in rows (day + name), at
    least 1. Small pages therefore get fewer write-in rows instead of overflowing.
    """

    id = "important_dates"
    name = "Important dates"
    category = "optional"
    section = "optional"

    BLOCK_COLS = 2
    BLOCK_ROWS = 6
    MIN_ENTRIES = 1
    DAY_W = 8.0
    DAY_GAP = 2.0

    @classmethod
    def layout(cls, rows: int) -> int:
        """Write-in rows per month for ``rows`` baseline rows of content."""
        return max(cls.MIN_ENTRIES, rows // cls.BLOCK_ROWS - 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("dates.title"))

        entries = self.layout(g.rows)
        per = entries + 2
        span = g.columns // self.BLOCK_COLS
        for m in range(1, 13):
            r, c = divmod(m - 1, self.BLOCK_COLS)
            x, w = g.col(c * span, span)
            top = r * per
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(top))
            pdf.cell(w, g.baseline, s.month_name(m))
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_HAIRLINE)
            for k in range(entries):
                y = g.row(top + 2 + k)
                pdf.line(x, y, x + self.DAY_W, y)
                pdf.line(x + self.DAY_W + self.DAY_GAP, y, x + w, y)


@register
class Todo(BasePage):
    """To-do list, 1 page per instance: checkbox + task rule + due-date rule on every row.

    Single column on every size (two columns would make rules too short on b6/a5). Row 1 holds
    the column labels; every following baseline row (``layout(rows)``) is a task row, so the
    page is filled from b6 to letter. The due column is the last grid column, the task rule
    runs from the checkbox to the gutter before it. ``Todo(count=N)`` gives N pages (default 1);
    there is no config field for the count yet, like Notes/Contacts.
    """

    id = "todo"
    name = "To-do list"
    category = "optional"
    section = "optional"

    BOX = 3.0
    DUE_COLS = 1

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @staticmethod
    def layout(rows: int) -> int:
        """Task rows for ``rows`` baseline rows of content (one row is the label row)."""
        return max(0, rows - 1)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("todo.title"))

        _draw_task_list(
            pdf, g, 0, self.layout(g.rows), (s("todo.task"), s("todo.due")), self.BOX, self.DUE_COLS
        )


@register
class Projects(BasePage):
    """Project planner, 1 page per instance (one project per page).

    Top to bottom: project and objective rows, a start | deadline row, 1 gap row, the task list
    (label row + task rows) , 1 gap row and a notes block (label row + plain rules).
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure; of the rest, notes get a third
    (at least ``MIN_NOTES``) and tasks the remainder, so small pages shrink both instead of
    overflowing. ``Projects(count=N)`` gives N pages (default 1); no config field yet.
    """

    id = "projects"
    name = "Project planner"
    category = "optional"
    section = "optional"

    FIELD_ROWS = 3
    FIXED_ROWS = FIELD_ROWS + 4  # fields, gap, task labels, gap, notes label
    MIN_NOTES = 2
    LABEL_W = 22.0
    BOX = 3.0
    DUE_COLS = 1

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int]:
        """(task rows, notes rows) for ``rows`` baseline rows of content."""
        free = max(0, rows - cls.FIXED_ROWS)
        notes = min(free, max(cls.MIN_NOTES, free // 3))
        return free - notes, notes

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("projects.title"))

        tasks, notes = self.layout(g.rows)
        x, w = g.safe.x, g.safe.w
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        draw_label_rule(pdf, x, w, g.row(1), s("projects.name"), self.LABEL_W)
        draw_label_rule(pdf, x, w, g.row(2), s("projects.objective"), self.LABEL_W)
        span = g.columns // 2
        lx, lw = g.col(0, span)
        rx, rw = g.col(span, g.columns - span)
        draw_label_rule(pdf, lx, lw, g.row(3), s("projects.start"), self.LABEL_W)
        draw_label_rule(pdf, rx, rw, g.row(3), s("projects.deadline"), self.LABEL_W)

        tr = self.FIELD_ROWS + 1
        labels = (s("projects.task"), s("projects.due"))
        _draw_task_list(pdf, g, tr, tasks, labels, self.BOX, self.DUE_COLS)

        nr = tr + tasks + 2
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(x, g.row(nr))
        pdf.cell(w, g.baseline, s("projects.notes"))
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(notes):
            y = g.row(nr + 2 + k)
            pdf.line(x, y, x + w, y)


@register
class Budget(BasePage):
    """Monthly budget, 1 page per month (12 instances): sections and a summary block.

    Sections in order: income, fixed expenses, variable expenses, savings. Each is a label row
    (section name, "Amount" over the amount column) then write-in rows of description rule +
    amount rule; the amount column is the last ``AMOUNT_COLS`` grid columns. A gap row follows
    each section, then the summary: total income, total expenses, balance (label + amount rule).
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (4 labels, 4 gaps, 3 summary rows);
    the rest is split by ``WEIGHTS`` (rounded down, leftovers go to the heaviest sections first),
    so small pages get fewer write-in rows instead of overflowing.
    """

    id = "budget"
    per_month = True
    name = "Monthly budget"
    category = "optional"
    section = "optional"

    WEIGHTS = (1, 2, 2, 1)
    SUMMARY_ROWS = 3
    FIXED_ROWS = len(WEIGHTS) * 2 + SUMMARY_ROWS
    AMOUNT_COLS = 2

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int, int, int]:
        """Write-in rows for (income, fixed, variable, savings) given ``rows`` content rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        total = sum(cls.WEIGHTS)
        counts = [free * wt // total for wt in cls.WEIGHTS]
        left = free - sum(counts)
        for i in sorted(range(len(counts)), key=lambda i: -cls.WEIGHTS[i]):
            if left <= 0:
                break
            counts[i] += 1
            left -= 1
        return counts[0], counts[1], counts[2], counts[3]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("budget.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x = g.safe.x
        ax, aw = g.col(g.columns - self.AMOUNT_COLS, self.AMOUNT_COLS)
        desc_w = ax - g.gutter - x
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)

        r = 0
        keys = ("income", "fixed", "variable", "savings")
        for key, n in zip(keys, self.layout(g.rows), strict=True):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(r))
            pdf.cell(desc_w, g.baseline, s(f"budget.{key}"))
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
            pdf.set_xy(ax, g.row(r))
            pdf.cell(aw, g.baseline, s("budget.amount"))
            for k in range(n):
                y = g.row(r + 2 + k)
                pdf.line(x, y, x + desc_w, y)
                pdf.line(ax, y, ax + aw, y)
            r += n + 2

        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        for k, key in enumerate(("total_income", "total_expenses", "balance")):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_xy(x, g.row(r + k))
            pdf.cell(desc_w, g.baseline, s(f"budget.{key}"), align="R")
            pdf.line(ax, g.row(r + k + 1), ax + aw, g.row(r + k + 1))


@register
class Habits(BasePage):
    """Monthly habit tracker, 1 page per month (12 instances): habits x days grid of circles.

    Header row (baseline row 0) holds the month title; row 1 the day numbers over the day
    columns; then one baseline row per habit. The name write-in column is the first
    ``NAME_COLS`` grid columns (plus gutter); the days of *that* month (28-31, from the calendar)
    share the remaining width equally, so cell width = remaining width / days. Each cell holds a
    small circle (``CIRCLE_RATIO`` of the smaller of cell width and row height). Weekend columns
    get the ``weekend_fill`` tint behind the grid.
    Fit rule (``layout(rows)``): habits = ``rows - HEADER_ROWS`` (title + day numbers), capped
    at ``MAX_HABITS``; never negative.
    """

    id = "habits"
    per_month = True
    name = "Habit tracker"
    category = "optional"
    section = "optional"

    HEADER_ROWS = 2
    MAX_HABITS = 20
    NAME_COLS = 2
    CIRCLE_RATIO = 0.7

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int, max_habits: int = MAX_HABITS) -> int:
        """Habit rows that fit in ``rows`` content rows, at most ``max_habits``."""
        return max(0, min(max_habits, rows - cls.HEADER_ROWS))

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        month, year = ctx["month"], ctx["year"]
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("habits.title", month=s.month_name(month), year=year))

        x = g.safe.x
        days = days_in_month(year, month)
        n = self.layout(g.rows, config.habits_max)
        name_w = g.span_width(self.NAME_COLS)
        gx = x + name_w + g.gutter
        cell_w = (g.safe.x2 - gx) / days
        diam = min(cell_w, g.baseline) * self.CIRCLE_RATIO

        pdf.set_fill_color(*color(pdf, "weekend_fill"))
        for d in range(days):
            if date(year, month, d + 1).weekday() >= 5:
                pdf.rect(gx + d * cell_w, g.row(1), cell_w, (n + 1) * g.baseline, style="F")

        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(
            font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[0]
        )  # regular: narrower digits
        pdf.set_xy(x, g.row(1))
        pdf.cell(name_w, g.baseline, s("habits.habit"))
        for d in range(days):
            pdf.set_xy(gx + d * cell_w, g.row(1))
            pdf.cell(cell_w, g.baseline, str(d + 1), align="C")

        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(n):
            top = g.row(2 + k)
            pdf.line(x, top + g.baseline, x + name_w, top + g.baseline)
            for d in range(days):
                draw_circle(pdf, gx + (d + 0.5) * cell_w, top + g.baseline / 2, diam)


@register
class MonthlyReview(BasePage):
    """Monthly review, 1 page per month (12 instances): four write-in sections and a rating.

    Sections in order: wins, challenges, lessons, goals for next month (checkbox rows). Each is
    a label row, ``n`` write-in rules and a gap row; the last row holds the satisfaction label
    and ``RATING`` small circles (1 to 5) right-aligned, ``CIRCLE_PITCH`` baselines apart.
    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (4 labels, 4 gaps, 1 rating row);
    the rest is split equally among the sections, leftover rows going to the first sections, so
    small pages get fewer rules instead of overflowing. Never negative.
    """

    id = "monthly_review"
    per_month = True
    name = "Monthly review"
    category = "optional"
    section = "optional"

    SECTIONS = ("wins", "challenges", "lessons", "goals")
    FIXED_ROWS = len(SECTIONS) * 2 + 1
    RATING = 5
    CIRCLE_RATIO = 0.7
    CIRCLE_PITCH = 2.0  # in baselines
    BOX_RATIO = 0.6  # checkbox side as a fraction of a baseline

    def instances(self, config: Config) -> list[Ctx]:
        return month_ctxs(config)

    @classmethod
    def layout(cls, rows: int) -> tuple[int, int, int, int]:
        """Write-in rows per section (wins, challenges, lessons, goals) for ``rows`` rows."""
        free = max(0, rows - cls.FIXED_ROWS)
        n = len(cls.SECTIONS)
        base, extra = divmod(free, n)
        counts = [base + (i < extra) for i in range(n)]
        return counts[0], counts[1], counts[2], counts[3]

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("review.title", month=s.month_name(ctx["month"]), year=ctx["year"]))

        x, w = g.safe.x, g.safe.w
        box = g.baseline * self.BOX_RATIO
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        r = 0
        for key, n in zip(self.SECTIONS, self.layout(g.rows), strict=True):
            pdf.set_text_color(*color(pdf, "accent"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            pdf.set_xy(x, g.row(r))
            pdf.cell(w, g.baseline, s(f"review.{key}"))
            for k in range(n):
                y = g.row(r + 2 + k)
                if key == "goals":
                    draw_checkbox(pdf, x, y - g.baseline + (g.baseline - box) / 2, box)
                    pdf.line(x + box + g.gutter, y, x + w, y)
                else:
                    pdf.line(x, y, x + w, y)
            r += n + 2

        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(x, g.row(r))
        pdf.cell(w, g.baseline, s("review.rating"))
        pitch = g.baseline * self.CIRCLE_PITCH
        diam = g.baseline * self.CIRCLE_RATIO
        x0 = g.safe.x2 - self.RATING * pitch
        for i in range(self.RATING):
            draw_circle(pdf, x0 + (i + 0.5) * pitch, g.row(r) + g.baseline / 2, diam)


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


def _ellipsize(pdf: FPDF, text: str, width: float) -> str:
    """``text`` cut to fit ``width`` in the current font, ending in "..." when cut."""
    if pdf.get_string_width(text) <= width:
        return text
    while text and pdf.get_string_width(text + "...") > width:
        text = text[:-1]
    return text.rstrip() + "..."


@register
class Holidays(BasePage):
    """Public holidays of ``config.year`` for ``config.holiday_country``, 1 page.

    One row (``ROW_BASELINES`` baselines tall) per holiday: short date + name, hairline below.
    Fit rule (``layout(rows, n)``): capacity ``cap = rows // ROW_BASELINES``. If the ``n`` holidays
    fit, one column; otherwise two columns (filled top to bottom, left first) showing the first
    ``min(n, 2 * cap)`` holidays; the rest are truncated, never drawn outside the safe area.
    No holidays (or an unsupported country code) => ``cap`` empty write-in rows (date + name).
    """

    id = "holidays"
    name = "Holidays"
    category = "optional"
    section = "optional"

    ROW_BASELINES = 2

    @classmethod
    def layout(cls, rows: int, n: int) -> tuple[int, int, int]:
        """(columns, shown, rows per column) for ``n`` holidays on ``rows`` content rows."""
        cap = rows // cls.ROW_BASELINES
        if n <= 0:
            return 1, 0, cap
        if n <= cap:
            return 1, n, n
        shown = min(n, 2 * cap)
        return 2, shown, -(-shown // 2)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        try:
            found = list(merged_holidays(config).items())
        except ValueError:
            found = []
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, f"{s('holidays.title')} {config.year} {config.holiday_country}".strip())

        cols, shown, per_col = self.layout(g.rows, len(found))
        rh = self.ROW_BASELINES
        col_w = (g.safe.w - (cols - 1) * g.gutter * 2) / cols if cols > 1 else g.safe.w
        date_w = g.col_width
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for i in range(max(shown, per_col)):
            c, k = divmod(i, per_col)
            x = g.safe.x + c * (col_w + g.gutter * 2)
            top, y = g.row(k * rh), g.row(k * rh + rh)
            pdf.line(x, y, x + col_w, y)
            if i >= shown:
                continue
            d, name = found[i]
            pdf.set_text_color(*color(pdf, "muted"))
            pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
            mon = s.month_name(d.month, short=True)
            when = f"{d.day} {mon.lower()}" if config.language == "es" else f"{mon} {d.day}"
            pdf.set_xy(x, top + (rh - 1) * g.baseline)
            pdf.cell(date_w, g.baseline, when)
            pdf.set_text_color(*color(pdf, "ink"))
            pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[1])
            nw = col_w - date_w - g.gutter
            pdf.set_xy(x + date_w + g.gutter, top + (rh - 1) * g.baseline)
            pdf.cell(nw, g.baseline, _ellipsize(pdf, name, nw))


@register
class Passwords(BasePage):
    """Passwords page with a warning, 1 page per instance.

    Top to bottom: a bordered warning box (``WARN_ROWS`` baseline rows, a triangle icon drawn
    with lines plus wrapped text), 1 gap row, a label row (Site / User / Password or hint) and
    write-in entries of ``ROW_BASELINES`` rows each in three columns separated by a gutter.
    Fit rule (``layout(rows)``): entries = ``(rows - FIXED_ROWS) // ROW_BASELINES``, never
    negative, so small pages get fewer entries instead of overflowing. ``Passwords(count=N)``
    gives N pages (default 1, repetition "1-2"); no config field yet, like Todo.
    """

    id = "passwords"
    name = "Passwords"
    category = "optional"
    section = "optional"

    WARN_ROWS = 4
    FIXED_ROWS = WARN_ROWS + 2  # warning, gap, label row
    ROW_BASELINES = 2
    COLUMNS = 3

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, rows: int) -> int:
        """Entry rows for ``rows`` baseline rows of content."""
        return max(0, (rows - cls.FIXED_ROWS) // cls.ROW_BASELINES)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("passwords.title"))

        # Warning box: rows 0..WARN_ROWS, border, triangle icon, wrapped text.
        x, w = g.safe.x, g.safe.w
        top, bottom = g.row(0), g.row(self.WARN_ROWS)
        pdf.set_draw_color(*color(pdf, "accent"))
        pdf.set_line_width(tokens.STROKE_REGULAR)
        pdf.rect(x, top, w, bottom - top)
        icon = min(2 * g.baseline, bottom - top - 2 * g.gutter)
        ix, iy = x + g.gutter, top + (bottom - top - icon) / 2
        pdf.set_line_width(tokens.STROKE_LIGHT)
        pdf.polygon([(ix + icon / 2, iy), (ix + icon, iy + icon), (ix, iy + icon)])
        pdf.line(ix + icon / 2, iy + icon * 0.35, ix + icon / 2, iy + icon * 0.65)
        pdf.line(ix + icon / 2, iy + icon * 0.78, ix + icon / 2, iy + icon * 0.85)
        tx = ix + icon + g.gutter
        pdf.set_text_color(*color(pdf, "ink"))
        pdf.set_font(font(pdf, "secondary"), "", tokens.TYPE_SIZES_PT[1])
        pdf.set_xy(tx, top + g.baseline / 2)
        pdf.multi_cell(
            x + w - g.gutter - tx,
            g.baseline,
            s("passwords.warning"),
            max_line_height=g.baseline,
            new_x="LEFT",
            new_y="NEXT",
        )

        col_w = (w - (self.COLUMNS - 1) * g.gutter) / self.COLUMNS
        label_row = self.WARN_ROWS + 1
        labels = (s("passwords.site"), s("passwords.user"), s("passwords.password"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_text_color(*color(pdf, "muted"))
        for c, label in enumerate(labels):
            pdf.set_xy(x + c * (col_w + g.gutter), g.row(label_row))
            pdf.cell(col_w, g.baseline, label)
        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for k in range(self.layout(g.rows)):
            y = g.row(label_row + (k + 1) * self.ROW_BASELINES)
            for c in range(self.COLUMNS):
                cx = x + c * (col_w + g.gutter)
                pdf.line(cx, y, cx + col_w, y)
