# Phase 3 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as before (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Pages live in `agenda/pages/{core,optional,value_added}.py` and subclass `agenda.pages.base.BasePage`.
- Test helpers in `tests/helpers.py` (`from helpers import ...`): `render_page(page_cls, cfg) -> bytes` (all instances), `assert_in_safe_area(pdf_bytes, cfg)` (text origins + rect/line vertices per page; needs debug_grid False). Use both in every page test.
- Calendar logic comes from `agenda/calendar.py`; geometry from `Grid` (never hardcode mm).

## Log

### Task 1: BasePage
- `agenda/pages/base.py`: ABC `BasePage` with ClassVars `id`, `name`, `category`, `section`, `pages=1`, `starts_on="any"`; constants `CATEGORIES`, `SECTIONS`, `STARTS_ON`; `validate_page_class(cls)`.
- Validation runs in `__init_subclass__` for concrete classes (draw overridden) and raises ValueError; abstract intermediates may omit attributes.
- ctx = plain `dict` (e.g. `{"month": 3}`); `instances(config) -> list[ctx]` defaults to `[{}]`.
- `draw(pdf, ctx, config, grids)`: caller adds `pages` pages with `exporter.add_page` and passes their grids in order; `pdf.page` is the last one, so a spread sets `pdf.page = pdf.page - 1` to draw the left page. Pages never add pages or fillers.
- Instances are created without args: `Page().instances(cfg)`. `@register` (task 2) should validate nothing extra beyond unique `id`.
### Task 2: catalog
- `agenda/catalog.py`: `register` (dup id -> ValueError, non-BasePage -> TypeError), `get_page` (unknown -> KeyError listing ids), `all_pages`, `pages_by_category`, `resolve_pages(config)` (None = core pages in registration order; presets not handled).
- Page modules import `register` from `agenda.catalog`; the catalog imports them lazily in `load_pages()` (called by every lookup), so no cycle. `CATALOG` dict is the raw registry.
- Core registration order = display order for `pages=None`; a later task (Phase 4 plan) does section ordering. Tests snapshot/restore `catalog.CATALOG`.


### Task 3: Cover
- `agenda/pages/core.py`: `Cover` (`cover`, core, front_back, 1 page): tint panel (top 2/3 of content rows) with accent bar, title (18pt, `cover.title`) and year (28pt bold). Existing i18n keys reused, none added.
- Safe-area check sees text origins only; keep cells within `safe`. Inter via `pdf.set_font("Inter", style, pt)`; set `pdf.c_margin = 0` for cells on the grid.

### Task 4: Personal information
- `agenda/pages/core.py`: `PersonalInfo` (`personal_info`, core, front_back, 1 page); heading + `FIELDS` (i18n `personal.*` keys, none added). Label 1 row, write-in lines at row bottoms (hairline, `line` color), 2 rows for address, 1 gap row between fields.
- Fields that don't fit the page rows are dropped (all fit on B6/A5/half-letter/A4). Lines span full content width, so no helper added to draw.py.

### Task 5: Yearly
- `Yearly` (`yearly`, core, front_back, 1 page; 3x4 mini months, each 2 grid columns; year in header band). Chose 1 page, so `starts_on="any"`.
- Reusable: `agenda.draw.draw_mini_month(pdf, rect, year, month, lang, week_start, day_style, title_pt, body_pt)` (8 equal lines, 7 equal columns; adjacent-month days left blank) and `DayStyle(color, fill)`.
- Task 12 hook: `Yearly.day_style(date) -> DayStyle | None` (staticmethod, returns None); pass the same callable to `draw_mini_month` on monthly.

### Task 6: Monthly
- `Monthly` (`monthly`, core, section monthly, 1 page, starts_on any; 12 ctxs `{"month": m}`). Header `month.title`, weekday row (short), day boxes from `month_grid` (blank boxes for adjacent months), priorities block (1/5 of rows) at the bottom.
- `Monthly.day_style(date)` hook like Yearly (None); fills boxes and colors the day number.

### Task 7: Weekly
- `Weekly` (`weekly`, core, section weekly, 2 pages, starts_on left). ctx: `number`, `iso_year`, `days` (7 dates, week_start order, may span years), `month` (owner, from `weeks_by_month`; instances in that page order).
- Layout: 4 equal blocks per page; left = days 1-4, right = days 5-7 + notes block (`notes.title`). Header: week number (left), localized month(s)/year (right). `Weekly.day_style` hook (None) fills the day label row.
- Draws left page via `pdf.page = last - 1`, then restores. Tests use a leading blank page (page 1 is right) via `render_spreads` in tests/test_weekly.py; `assert_in_safe_area(..., allow_blank=True)` added.
