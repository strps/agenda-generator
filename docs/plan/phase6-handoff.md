# Phase 6 handoff

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Value-added pages live in `agenda/pages/value_added.py`, subclass `BasePage`, use `@register`, category and section `value_added`; ids come from plan §3.3. They appear in the plan only when listed in `config.pages`.
- `draw(pdf, ctx, config, grids)`: `grids[0]` is the page's `Grid`; never hardcode mm (use `g.header/content/safe/rows/row(n)/baseline`, `tokens`).
- Header: `pdf.c_margin = 0`, Inter bold `TYPE_SIZES_PT[3]` accent in `g.header`; strings via `Strings(config.language)("key", n=...)`, keys in both es and en in `agenda/i18n.py`.
- x12 pages: `instances` returns `month_ctxs(config)`. Helpers in `agenda/draw.py`: `draw_checkbox`, `draw_circle`, `draw_label_rule`, `draw_pattern`.
- Tests: `from helpers import render_page, assert_in_safe_area, drawn_points`; no emoji, draw shapes. See `tests/test_monthly_quotes.py`.

## Log
### Tasks 1-5 (quotes, vision_board, health, meals, gratitude)
- Each page has `layout(rows)` in its class docstring; quotes/health are x12 via `month_ctxs`; gratitude takes `count=N`; `draw_mood` and `MOOD_LEVELS` live in `agenda/draw.py`.
### Task 6: Books, movies, series
- `Media(count=1)` (`media_log`, value_added/value_added; catalog gives value 3, no repetition, so `count=N`, negatives rejected). Type column = stacked Book/Movie/Series labels, title, date, 5 `draw_circle` rating.
- `layout(rows, width, type_w, date_w, title_min, g) -> MediaLayout(rows, circle_d, show_date)`: rows = (rows-1)//3; shrinks circles (ratios of a baseline) before dropping the date column. Grid has 6 columns, so DATE_COLS=1, TITLE_COLS=2. Today all sizes keep the date.
- Strings `media.title/type/book/movie/series/name/date/rating` (es, en).
### Task 7: Travel planner
- `Travel(count=1)` (`travel`, value_added/value_added; catalog gives value 4, no repetition, so `count=N`, negatives rejected). Fields destination, from|to, budget; itinerary "Day N" + rule rows; packing checkbox rows.
- `layout(rows) -> TravelLayout(day_rows, pack_rows, pack_cols)`: `FIXED_ROWS` structure, free rows split 60% itinerary (capped at `MAX_DAYS`, extra goes to packing) / rest packing; 2 packing columns when rows >= 30 (a5, letter).
- Strings `travel.title/destination/from/to/budget/itinerary/day/packing` (es, en).
### Task 8: 30-day challenges
- `Challenge30(count=1)` (`challenges30`, value_added/value_added; catalog gives value 4, no repetition, so `count=N`, negatives rejected). Fields "My challenge"/"Why", 30 hairline day cells (number top-left, `draw_circle` tick), "Reflection" rules.
- `layout(rows) -> ChallengeLayout(cols, grid_rows, cell_rows, reflect_rows)`: cols 5x6 or 6x5 (tile 30 exactly); tallest cell (4..2 baselines) that leaves >= 2 reflection rules, ties to 5 cols. b6 = 6x5 cells of 4 rows; a5/letter = 5x6.
- Strings `challenge.title/mine/why/reflection` (es, en).
### Task 9: Idea map
- `IdeaMap(count=1)` (`ideas`, value_added/value_added; catalog gives value 3, no repetition, so `count=N`, negatives rejected). Canvas = `g.content`; `layout(w, h) -> IdeaLayout(centre, centre_radii, sat_radii, satellites)` relative to canvas top-left.
- Satellites evenly spaced by angle on an ellipse (first at top, clockwise); 8 when w >= 0.78*h (letter) else 6 (a5, b6). All radii are ratios of w/h; rules inside each shape.
- Strings `ideas.title/main` (es, en).
### Task 10: QR codes
- `QRCodes` (`qr`, value_added/value_added); `qrcode` was already a dependency (no new one). New `Config.qr_urls: list[str]` (default empty; stripped, non-empty, <= `QR_MAX_CHARS`=200, <= `QR_MAX_COUNT`=24; any text allowed, not only http). Not added to the argparse CLI.
- `layout(w, h, baseline, gutter) -> QRLayout(cols, rows, cell_w, cell_h, side)`: 2 cols, 3 rows if it keeps the QR square >= 0.8 cell width, else 2 (all sizes give 2x2). `instances` = ceil(urls/per_page) ctxs `{"urls": [...]}`; 0 URLs = 0 pages (build_plan fine).
- Modules are filled `re` rects (ECC M, 4-module quiet zone); caption = shortened text + "Name" rule. Strings `qr.title/label` (es, en).
### Task 11: Physical extras guide
- `ExtrasGuide` (`physical_extras` from catalog §3.3, value 5; value_added/value_added, 1 page, no `count`). `layout(rows) -> ExtrasLayout(tips, supply_rows)`: each tip = `TIP_ROWS` (3) rows, `min(6, rows//3)` tips in order; leftover rows >= 2 give a "My supplies" checkbox list (<= 4). All sizes show 6 tips.
- Icons drawn by `ExtrasGuide._icon(pdf, kind, x, y, d)` from rect/ellipse/line. Strings `extras.title/supplies/fold/stickers/tabs/ribbon/loop/pocket` (es, en); text clipped to 2 lines.
### Task 12: Niche packs
- Catalog lists `niche_*` (value 5), so ids are `niche_entrepreneur/student/fitness` (`PackEntrepreneur/PackStudent/PackFitness`, value_added/value_added, `count=N` via shared `_Counted` base, negatives raise). No config field; list ids in `config.pages`.
- `layout(rows)`: entrepreneur -> `(metric_rows, pipeline_rows, decision_rows)`; student -> `(table_rows, study)` (study-hours block dropped on tiny pages); fitness -> `(exercise_rows, notes_rows)`. Rules in class docstrings.
- Strings `entre.*`, `student.*`, `fitness.*` (es, en). Tests: `tests/test_niche_packs.py`.

## Phase 6 wrap-up (open items for later phases)
- Presets: `added_value` ClassVar on `BasePage` (0 = unscored: core/optional); `preset_pages(name)` in catalog (essential >= 5, complete >= 4, premium = all non-core). `Config.preset` fills `pages` when empty (explicit `pages` win); `--preset` added to the temporary CLI.
- Optional pages have no score in plan §3.2, so they are premium-only; give them scores if wanted in complete.
- Changing `preset` by assignment after pages were filled does not refill (pages not empty).
- Done-when: `tests/test_value_added_pages.py` (14 ids x es/en x 5 sizes + premium export).
- Pages with no catalog repetition use chosen defaults (health x12, others 1 / `count`).
- Phase 7: expose `count` and `qr_urls` in CLI/YAML; Phase 5 open items still open.
