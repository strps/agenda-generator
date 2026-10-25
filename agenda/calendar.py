"""Date calculations: months, days, month grids and ISO weeks (pure, no drawing).

Weekday indices follow `datetime`: 0 = Monday ... 6 = Sunday.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

WEEK_STARTS = ("monday", "sunday")


def weekday_order(week_start: str = "monday") -> list[int]:
    """Weekday indices (0=Mon..6=Sun) in column order for the given week start."""
    if week_start == "monday":
        return [0, 1, 2, 3, 4, 5, 6]
    if week_start == "sunday":
        return [6, 0, 1, 2, 3, 4, 5]
    raise ValueError(f"week_start must be one of {WEEK_STARTS}, got {week_start!r}")


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    if month == 2:
        return 29 if is_leap(year) else 28
    return 30 if month in (4, 6, 9, 11) else 31


def days_of_year(year: int) -> list[date]:
    """Every date of `year`, in order (365 or 366)."""
    start = date(year, 1, 1)
    return [start + timedelta(days=i) for i in range(366 if is_leap(year) else 365)]


def month_grid(year: int, month: int, week_start: str = "monday") -> list[list[date | None]]:
    """Rows of 7 columns (in `weekday_order`); cells outside the month are None.

    Between 4 and 6 rows; no leading padding if the 1st falls on the week start.
    """
    order = weekday_order(week_start)
    n = days_in_month(year, month)
    lead = order.index(date(year, month, 1).weekday())
    cells: list[date | None] = [None] * lead
    cells += [date(year, month, d) for d in range(1, n + 1)]
    cells += [None] * (-len(cells) % 7)
    return [cells[i : i + 7] for i in range(0, len(cells), 7)]


@dataclass(frozen=True)
class Week:
    """One ISO week laid out for a given week start.

    `number`/`iso_year` are always the ISO ones (of the week's Monday).
    `days` has 7 dates in `weekday_order`; `start`/`end` are days[0]/days[-1].
    """

    number: int
    iso_year: int
    days: list[date]

    @property
    def start(self) -> date:
        return self.days[0]

    @property
    def end(self) -> date:
        return self.days[-1]


def iso_weeks_in_year(year: int) -> int:
    """52 or 53. Dec 28 always lies in the last ISO week of its year."""
    return date(year, 12, 28).isocalendar()[1]


def weeks_of_year(year: int, week_start: str = "monday") -> list[Week]:
    """Every ISO week whose ISO year is `year`, in order.

    Week 1 may start in the previous year (and the last week may end in the next).
    Sunday start: the week keeps its ISO number but runs Sun..Sat, the Sunday
    being the day before the ISO Monday.
    """
    order = weekday_order(week_start)  # validates week_start
    first = date.fromisocalendar(year, 1, 1)
    shift = -1 if order[0] == 6 else 0
    weeks = []
    for n in range(1, iso_weeks_in_year(year) + 1):
        start = first + timedelta(weeks=n - 1, days=shift)
        weeks.append(Week(n, year, [start + timedelta(days=i) for i in range(7)]))
    return weeks


def week_month(week: Week) -> tuple[int, int]:
    """(year, month) that owns `week`: the month of its first day (`week.start`).

    The result may be (iso_year - 1, 12) for a week 1 that starts in the
    previous December; `weeks_by_month` places those under January.
    """
    return (week.start.year, week.start.month)


def weeks_by_month(year: int, week_start: str = "monday") -> dict[int, list[Week]]:
    """Group `weeks_of_year(year)` by owning month, keys 1..12 (all present).

    A week belongs to the month of its first day. Edge: a week 1 starting in
    the previous December goes under January of `year`. Every week appears
    exactly once; a month has 3-5 weeks.
    """
    result: dict[int, list[Week]] = {m: [] for m in range(1, 13)}
    for week in weeks_of_year(year, week_start):
        y, m = week_month(week)
        result[m if y == year else 1].append(week)
    return result
