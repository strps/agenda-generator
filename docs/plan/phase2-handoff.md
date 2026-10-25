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
- Next tasks can reuse `weekday_order` and `WEEK_STARTS`; ISO weeks not started.
