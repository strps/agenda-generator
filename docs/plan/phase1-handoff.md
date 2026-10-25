# Phase 1 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` (`.venv` is gitignored; already created, editable install, so code changes apply immediately).
- Run: `.venv/bin/agenda-gen ...` or `.venv/bin/python -m agenda ...`.
- Tests: `.venv/bin/pytest` (tests in `tests/`, `testpaths` set in pyproject).
- Lint: `.venv/bin/ruff check .` (line length 100, py311+, Python 3.13 locally).
- Layout: package `agenda/` at repo root (not `agenda_gen/`); setuptools discovers `agenda*`.
- CLI uses stdlib `argparse` (not typer); entry is `agenda.__main__:main(argv=None) -> int`.
- Deps (core): fpdf2, pydantic, PyYAML, holidays, pypdf, qrcode, Pillow. Extras: `gui` (PySide6, pypdfium2), `dev` (pytest, ruff).
- Fonts: top-level `assets/fonts/`; Inter registered by `new_document` (see Task 6).

## Log

### Tasks 1-2: layout
- `agenda/__main__.py`: `build_parser()`, `main(argv) -> int`. Stub modules exist for everything in plan §4 plus `i18n`, `pages/*`; fill in place. `tests/test_smoke.py` `MODULES` lists them; add new modules there.
- Gotcha: `agenda/calendar.py` shadows stdlib only for relative imports; use `from agenda import calendar`, never run scripts from inside `agenda/`.

### Task 3-4: config, sizes
- `agenda/config.py`: `Config` (pydantic, extra="forbid"); `page_size` is a normalized str; `Config.page_dimensions` -> final (w, h) mm. `agenda/sizes.py`: `parse_size`, `resolve_size`; orientation normalizes w/h.
- Not done (later): YAML loading, CLI overlay, presets, margin-vs-page-size checks.

### Tasks 5-6: exporter, fonts
- `agenda/exporter.py`: `new_document(cfg)` (mm, auto page break off, margins 0, Inter registered), `write_pdf`, `export_blank`. Fonts: `pdf.set_font("Inter", "", 10)`; styles `""`, `"B"`, `"I"`, `"BI"`; missing files raise `FontsMissingError` (CLI exit 1; invalid config exit 2).
- CLI temp flags `-o`, `--pages`, `--page-size`, `--orientation`; replace with real CLI later.
- Gotcha: fpdf2 `cell()` stays on the line by default; pass `new_x="LMARGIN", new_y="NEXT"` for line breaks.

### Task 7: tokens + grid
- `agenda/tokens.py`: constants (`COLUMNS=6`, `GUTTER=3`, `BASELINE=5`, `MARGIN_TOP/BOTTOM=10`, `HEADER_HEIGHT`, `FOOTER_HEIGHT`, colors, type sizes...).
- `agenda/grid.py`: frozen `Grid` + `Rect(x,y,w,h)`; origin top-left. Props `safe`, `header`, `footer`, `content`, `col_width`, `rows`; methods `col_x(i)`, `col(i, span)`, `row(n)`, `snap(y)`, `span(col, cols, row, rows)`. Columns 0-based. Top/bottom/header/footer come from tokens, not Config.

### Task 8: alternating margins
- `grid.side_for_page(n)`: 1-based; odd = "right" (recto, page 1), even = "left". Single source of truth; matches layout-grid.md (inner = binding side) and booklet convention (cover is recto).
- `Grid.for_page(cfg, n)`; `Grid.from_config(cfg, side)` / `for_side(side)` verified: right => left margin = inner, left => right margin = inner.
- `exporter.add_page(pdf, cfg) -> Grid`: adds the next page (n = pdf.page + 1), sets fpdf `l_margin`/`r_margin` to grid.left/right (top/bottom margins stay 0), moves cursor to `grid.safe` top-left, returns the page's Grid. `add_blank_pages(pdf, n, cfg)` now requires cfg. Always use `add_page` instead of `pdf.add_page()`.
- Task 9 overlay: call `grid = add_page(pdf, cfg)` per page and draw from `grid.safe/header/footer/content/col_x/row`.
- Gotcha: if a filler/blank page is inserted, page number = physical position, so side follows automatically.
- `ruff format` applied to all Python files (use `ruff format --check agenda tests`).

### Task 9: --debug-grid
- `agenda/draw.py::draw_debug_grid(pdf, grid, page_no=None)`: inner margin blue, outer orange, header/content/footer boxes, 6 columns (pink), 5 mm baselines, mm rulers on top/left edges (Inter 4 pt), label "p.N side". Restores colors/line width.
- `add_page` calls it when `cfg.debug_grid` (drawn at page creation, so page content added later paints over it; if that matters, move the call to a finalize step). CLI `--debug-grid` sets `Config.debug_grid`.
- Default size is half_letter, so `agenda-gen --debug-grid` yields 4 pages; visually verified pages 1-2 (margins swap, 15 mm inner / 10 mm outer). Render with `pdftoppm -r 110 -png`.
