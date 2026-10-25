# Phase 2 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as Phase 1 (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Date logic lives in `agenda/calendar.py`: pure functions, no fpdf, no drawing. Import as `from agenda.calendar import ...` (never `import calendar` from inside `agenda/`).
- Weekday indices are `datetime`'s: 0=Mon..6=Sun. `week_start` is `"monday"|"sunday"` (as in `Config`).
- Localized names come from `agenda/i18n.py`; do not duplicate them in `calendar.py`.

## Log

### Task 1: months, days, month grids
- `calendar.py`: `weekday_order(ws)` (Sun start -> `[6,0,..5]`, ValueError otherwise), `is_leap`, `days_in_month(y, m)`, `days_of_year(y) -> list[date]`, `month_grid(y, m, ws) -> list[list[date | None]]`.
- `month_grid`: rows of 7 in `weekday_order`; padding is `None` (not adjacent-month dates); 4-6 rows, no leading padding if the 1st is the week start.
- Next tasks can reuse `weekday_order` and `WEEK_STARTS`.

### Task 2: ISO weeks
- `calendar.py`: `Week(number, iso_year, days, start, end)` frozen; `iso_weeks_in_year(y)` (52/53); `weeks_of_year(y, ws)` = every ISO week with iso_year == y (week 1 may start in Dec of y-1, last may end in Jan of y+1, e.g. 2026 wk1 = Mon 2025-12-29).
- Not every day of `y` is in `weeks_of_year(y)`: Jan 1-3 2027 are in 2026 wk 53. Whole-year coverage = union of consecutive years, each day exactly once.
- Sunday start: ISO number kept, days = Sun..Sat with Sunday = ISO Monday - 1 (2026 wk1 = Sun 2025-12-28). Edge: a Sun Dec 31 opens next year's wk 1, so it is absent from that year's weeks.
- Weeks are not yet assigned to months (task 3).

### Task 3: weeks -> months
- `calendar.py`: `week_month(week) -> (year, month)` of `week.start`; `weeks_by_month(y, ws) -> {1..12: [Week]}` (all keys present, partition of `weeks_of_year`, in order).
- Week 1 starting in previous Dec (2026: Mon 12-29 / Sun 12-28) is filed under January of `y`, though `week_month` returns (y-1, 12). Last week starting in Dec stays in Dec.
- Mar 30 - Apr 5 2026 is March's; April's first week starts Apr 6. Page order: month -> its weeks (spread + dailies).

### Task 4: holidays
- `calendar.py`: `holidays_for(year, country="CR", language="es") -> dict[date, str]`, sorted; same-day names joined "; ". Imports `holidays` lazily.
- Language: `en`->`en_US` via prefix match; unsupported -> country default (no crash). Unknown country -> ValueError. Subdivisions not supported.
- `Config.holiday_country` only uppercases; it does not validate the code (error surfaces at `holidays_for`).
