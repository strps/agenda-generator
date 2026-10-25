# Phase 3 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as before (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Pages live in `agenda/pages/{core,optional,value_added}.py` and subclass `agenda.pages.base.BasePage`.
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

