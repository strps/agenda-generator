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
### Task 9: Notes
- `Notes` (`notes`, section front_back, 1 page): header `notes.title` + `draw_pattern(pdf, g.content, config.notes_pattern, g.baseline)` (agenda/draw.py; lined/dotted/grid/blank, anchored top-left of rect, clipped to it).
- Count: `Notes(count=N).instances(cfg)` -> N empty ctxs (default 1; spec says "variable"). Phase 4 padding: instantiate `Notes(count=missing)`; catalog default instance gives 1.
- Dots are zero-length round-cap lines (0.4 mm); blank draws only the header.
### Task 10: Contacts
- `Contacts` (`contacts`, section front_back, 1 page): header `contacts.title`; entries of name/phone/email label+rule rows (3 rows + 1 gap), 2 columns if safe width >= 100 mm.
- Count: `Contacts(count=N)` like `Notes` (default 1, N empty ctxs, ValueError if negative). Strings already existed. `notes` section was already front_back.
### Task 11: Back cover
- `BackCover` (`back_cover`, section front_back, 1 page) in core.py; shares `_cover_panel(pdf, g, title, year)` with `Cover` (Cover refactored, output unchanged).
- New i18n key `back_cover.line` (es "Que cada día cuente", en "Make every day count"); placement last is Phase 4.
