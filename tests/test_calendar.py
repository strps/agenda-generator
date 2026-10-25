from datetime import date

import pytest

from agenda.calendar import (
    days_in_month,
    days_of_year,
    holidays_for,
    is_leap,
    iso_weeks_in_year,
    month_grid,
    week_month,
    weekday_order,
    weeks_by_month,
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


def test_week_month_is_month_of_first_day():
    w = next(w for w in weeks_of_year(2026) if w.start == date(2026, 3, 30))
    assert w.end == date(2026, 4, 5)
    assert week_month(w) == (2026, 3)
    # Sunday start: Sun Mar 29 - Sat Apr 4 is March's
    ws = next(w for w in weeks_of_year(2026, "sunday") if w.start == date(2026, 3, 29))
    assert week_month(ws) == (2026, 3)


def test_weeks_by_month_mid_week_first_not_owned():
    by = weeks_by_month(2026)
    assert set(by) == set(range(1, 13))
    # Apr 1 2026 is a Wednesday: the week Mar 30 - Apr 5 is March's, April starts Apr 6
    assert by[4][0].start == date(2026, 4, 6)
    assert by[3][-1].start == date(2026, 3, 30)


@pytest.mark.parametrize("year", [2020, 2024, 2025, 2026, 2027, 2028])
@pytest.mark.parametrize("ws", ["monday", "sunday"])
def test_weeks_by_month_partition(year, ws):
    by = weeks_by_month(year, ws)
    flat = [w for m in range(1, 13) for w in by[m]]
    assert flat == weeks_of_year(year, ws)  # each once, in order
    for m, weeks in by.items():
        assert 3 <= len(weeks) <= 5  # Sunday-start Dec can lose its last week
        for w in weeks:
            y, mm = week_month(w)
            assert (y, mm) == (year, m) or (m == 1 and (y, mm) == (year - 1, 12))


def test_week_one_from_previous_december_goes_to_january():
    for ws, start in (("monday", date(2025, 12, 29)), ("sunday", date(2025, 12, 28))):
        first = weeks_by_month(2026, ws)[1][0]
        assert first.number == 1 and first.start == start


def test_holidays_cr_2026_known_dates():
    from agenda.calendar import holidays_for

    h = holidays_for(2026, "CR", "es")
    assert list(h) == sorted(h)
    assert h[date(2026, 1, 1)] == "Año Nuevo"
    assert h[date(2026, 4, 11)] == "Día de Juan Santamaría"
    assert date(2026, 7, 25) in h and date(2026, 9, 15) in h
    assert h[date(2026, 12, 25)] == "Navidad"
    assert all(d.year == 2026 for d in h)


def test_holidays_language_and_fallback():
    from agenda.calendar import holidays_for

    es, en = holidays_for(2026, "CR", "es"), holidays_for(2026, "CR", "en")
    assert es.keys() == en.keys()
    assert en[date(2026, 12, 25)] == "Christmas Day"
    assert es[date(2026, 12, 25)] != en[date(2026, 12, 25)]
    assert holidays_for(2026, "CR", "xx") == es  # CR default language is es
    assert holidays_for(2026, "cr", "es") == es


def test_holidays_other_country_and_invalid():
    from agenda.calendar import holidays_for

    us = holidays_for(2026, "US", "es")  # US has no es: falls back to English
    assert us[date(2026, 7, 4)] == "Independence Day"
    with pytest.raises(ValueError, match="XX"):
        holidays_for(2026, "XX")


@pytest.mark.parametrize("ws", ["monday", "sunday"])
@pytest.mark.parametrize("year,ndays,nweeks", [(2026, 365, 53), (2027, 365, 52), (2028, 366, 52)])
def test_phase2_done_when(year, ndays, nweeks, ws):
    days = days_of_year(year)
    assert len(days) == ndays
    assert any(d.month == 2 and d.day == 29 for d in days) == (year == 2028)
    assert iso_weeks_in_year(year) == nweeks
    weeks = weeks_of_year(year, ws)
    assert len(weeks) == nweeks
    by_month = weeks_by_month(year, ws)
    assert [w for m in range(1, 13) for w in by_month[m]] == weeks
    cells = [d for m in range(1, 13) for r in month_grid(year, m, ws) for d in r if d]
    assert sorted(cells) == days  # each day exactly once
    assert holidays_for(year)


def test_53_week_year_starting_thursday_vs_leap_starting_wednesday():
    assert date(2026, 1, 1).weekday() == 3 and not is_leap(2026)
    assert date(2020, 1, 1).weekday() == 2 and is_leap(2020)
    for y in (2020, 2026):
        assert iso_weeks_in_year(y) == 53
        assert weeks_of_year(y)[-1].number == 53
    assert date(2020, 12, 31).isocalendar()[:2] == (2020, 53)
    assert iso_weeks_in_year(2019) == 52 and iso_weeks_in_year(2021) == 52
