# Phase 3 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as before (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Pages live in `agenda/pages/{core,optional,value_added}.py` and subclass `agenda.pages.base.BasePage`.
- Test helpers in `tests/helpers.py` (`from helpers import ...`): `render_page(page_cls, cfg) -> bytes` (all instances), `assert_in_safe_area(pdf_bytes, cfg)` (text origins + rect/line vertices per page; needs debug_grid False). Use both in every page test.
- Calendar logic comes from `agenda/calendar.py`; geometry from `Grid` (never hardcode mm).

## Log

### Tasks 1-2: BasePage, catalog
- `agenda/pages/base.py`: ABC `BasePage` (ClassVars `id`, `name`, `category`, `section`, `pages=1`, `starts_on="any"`); validated in `__init_subclass__` (ValueError). ctx = plain dict; `instances(config)` defaults to `[{}]`.
- `draw(pdf, ctx, config, grids)`: caller adds the pages; `pdf.page` is the last one (a spread sets `pdf.page -= 1` for the left page). Pages never add pages.
- `agenda/catalog.py`: `register`, `get_page`, `all_pages`, `pages_by_category`, `resolve_pages(config)`; core registration order = display order. Tests snapshot/restore `catalog.CATALOG`.
### Tasks 3-4: Cover, PersonalInfo (`front_back`)
- Inter via `pdf.set_font("Inter", style, pt)`; set `pdf.c_margin = 0`. Safe-area check sees text origins only; keep cells in `safe`.
### Tasks 5-6: Yearly, Monthly
- `agenda.draw.draw_mini_month(pdf, rect, year, month, lang, week_start, day_style, title_pt, body_pt)`, `DayStyle(color, fill)`.
- Task 12 hook on each page: staticmethod `day_style(date) -> DayStyle | None` (None); Monthly ctx `{"month": m}`.
### Task 7: Weekly
- `Weekly` (2 pages, starts_on left). ctx: `number`, `iso_year`, `days` (7 dates), `month` (owner, `weeks_by_month` order). Tests use `render_spreads` in tests/test_weekly.py; `assert_in_safe_area(..., allow_blank=True)`.
### Task 8: Daily
- `Daily` (`daily`, section daily, 1 page). ctx `date`, `week`, `iso_year` (ISO; sort/place after its week's spread in Phase 4). `daily_months` NOT applied (Phase 4).
- Header: `day.title` + `week.number` right; schedule 06:00-21:00 left half (fewer hours if rows short), priorities/notes right. `Daily.day_style` fills header.
- Tests render a subset (`render_subset` in tests/test_daily.py), not all 366.
