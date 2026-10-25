"""Date calculations: months, days and month grids (pure, no drawing).

Weekday indices follow `datetime`: 0 = Monday ... 6 = Sunday.
"""

from __future__ import annotations

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
