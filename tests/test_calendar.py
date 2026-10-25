from datetime import date

import pytest

from agenda.calendar import (
    days_in_month,
    days_of_year,
    is_leap,
    iso_weeks_in_year,
    month_grid,
    weekday_order,
    weeks_of_year,
)


def test_weekday_order():
    assert weekday_order("monday") == [0, 1, 2, 3, 4, 5, 6]
    assert weekday_order("sunday") == [6, 0, 1, 2, 3, 4, 5]
    with pytest.raises(ValueError):
        weekday_order("friday")


@pytest.mark.parametrize("y,leap", [(2028, True), (2000, True), (1900, False), (2026, False)])
def test_leap_and_february(y, leap):
    assert is_leap(y) is leap
    assert days_in_month(y, 2) == (29 if leap else 28)
    assert len(days_of_year(y)) == (366 if leap else 365)


def test_days_in_month():
    assert [days_in_month(2026, m) for m in range(1, 13)] == [
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
    ]  # fmt: skip
    with pytest.raises(ValueError):
        days_in_month(2026, 13)


def test_days_of_year_bounds():
    d = days_of_year(2028)
    assert d[0] == date(2028, 1, 1) and d[-1] == date(2028, 12, 31)
    assert d[59] == date(2028, 2, 29)


@pytest.mark.parametrize("y", [2026, 2027, 2028])
@pytest.mark.parametrize("ws", ["monday", "sunday"])
def test_grid_invariants(y, ws):
    for m in range(1, 13):
        g = month_grid(y, m, ws)
        assert 4 <= len(g) <= 6 and all(len(r) == 7 for r in g)
        days = [c for r in g for c in r if c]
        assert days == [date(y, m, d) for d in range(1, days_in_month(y, m) + 1)]
        first = next(c for c in g[0] if c)
        assert g[0].index(first) == weekday_order(ws).index(first.weekday())


def test_no_leading_padding_when_first_is_week_start():
    # 2026-06-01 is Monday; 2026-02-01 is Sunday
    assert month_grid(2026, 6, "monday")[0][0] == date(2026, 6, 1)
    assert month_grid(2026, 2, "sunday")[0][0] == date(2026, 2, 1)
    # Feb 2026 Sun-start has 28 days from col 0: exactly 4 rows
    assert len(month_grid(2026, 2, "sunday")) == 4


def test_six_rows_and_padding():
    # 2026-03-01 is Sunday: Monday start pads 6, 31 days -> 6 rows
    g = month_grid(2026, 3, "monday")
    assert len(g) == 6 and g[0][:6] == [None] * 6 and g[0][6] == date(2026, 3, 1)
    assert g[-1][2:] == [None] * 5 and g[-1][1] == date(2026, 3, 31)
    assert len(month_grid(2026, 3, "sunday")) == 5


def test_leap_february_grid():
    g = month_grid(2028, 2, "monday")  # Feb 1 2028 is Tuesday
    assert g[0][:2] == [None, date(2028, 2, 1)]
    assert date(2028, 2, 29) in [c for r in g for c in r]


@pytest.mark.parametrize("year,n", [(2020, 53), (2026, 53), (2027, 52), (2028, 52)])
def test_iso_weeks_in_year(year, n):
    assert iso_weeks_in_year(year) == n
    assert len(weeks_of_year(year)) == n


def test_weeks_monday_overlap_and_iso_numbers():
    w = weeks_of_year(2026)
    assert (w[0].number, w[0].iso_year) == (1, 2026)
    assert w[0].start == date(2025, 12, 29)  # week 1 starts in the previous year
    assert w[-1].number == 53 and w[-1].end == date(2027, 1, 3)
    assert weeks_of_year(2027)[0].start == date(2027, 1, 4)
    for wk in w:
        assert len(wk.days) == 7 and wk.start.weekday() == 0
        assert wk.start.isocalendar()[:2] == (2026, wk.number)


def test_monday_weeks_cover_every_day_once():
    for y in (2026, 2027, 2028):
        days = [d for wk in weeks_of_year(y) for d in wk.days]
        assert len(days) == len(set(days))
    allw = [d for y in (2026, 2027, 2028) for wk in weeks_of_year(y) for d in wk.days]
    assert len(allw) == len(set(allw))
    for d in days_of_year(2027) + days_of_year(2028):
        assert d in allw


def test_weeks_sunday_start():
    w = weeks_of_year(2026, "sunday")
    assert w[0].number == 1 and w[0].start == date(2025, 12, 28)
    assert w[0].start.weekday() == 6 and w[0].end == date(2026, 1, 3)
    assert all(wk.start.weekday() == 6 and wk.end.weekday() == 5 for wk in w)
    # Jan 1 2023 is a Sunday: it opens ISO week 1 of 2023, not week 52 of 2022
    assert weeks_of_year(2023, "sunday")[0].start == date(2023, 1, 1)
    assert weeks_of_year(2022, "sunday")[-1].end == date(2022, 12, 31)
    with pytest.raises(ValueError):
        weeks_of_year(2026, "friday")
