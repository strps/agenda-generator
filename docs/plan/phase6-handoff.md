# Phase 6 handoff

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Value-added pages live in `agenda/pages/value_added.py`, subclass `BasePage`, use `@register`, category and section `value_added`; ids come from plan §3.3. They appear in the plan only when listed in `config.pages`.
- `draw(pdf, ctx, config, grids)`: `grids[0]` is the page's `Grid`; never hardcode mm (use `g.header/content/safe/rows/row(n)/baseline`, `tokens`).
- Header: `pdf.c_margin = 0`, Inter bold `TYPE_SIZES_PT[3]` accent in `g.header`; strings via `Strings(config.language)("key", n=...)`, keys in both es and en in `agenda/i18n.py`.
- x12 pages: `instances` returns `month_ctxs(config)`. Helpers in `agenda/draw.py`: `draw_checkbox`, `draw_circle`, `draw_label_rule`, `draw_pattern`.
- Tests: `from helpers import render_page, assert_in_safe_area, drawn_points`; no emoji, draw shapes. See `tests/test_monthly_quotes.py`.

## Log
### Task 1: Monthly quotes
- `MonthlyQuotes` (`quotes`, value_added/value_added, 1 page x12 via `month_ctxs`); `layout(rows) -> (quote rows, reflection rules)`: quote area = half the rows in whole 2-baseline lines, label row + rules below.
### Task 2: Vision board
- `VisionBoard` (`vision_board`, value_added/value_added, 1 page); `layout(rows, width_rows) -> VisionLayout(word_rows, cols, nrows, cell_rows)` in baseline units, derived from the safe area (see class docstring).
### Task 3: Health tracker
- `HealthTracker` (`health`, value_added/value_added, 1 page x12 via `month_ctxs`; the catalog gives no repetition, chosen monthly like Habits). `layout(rows)` = tracker rows that fit (2 baselines each, never shrunk; trackers dropped from the end); all 5 fit on a5/b6/letter.
- `draw_mood(pdf, cx, cy, d, level 1..5)` and `MOOD_LEVELS` in `agenda/draw.py`: circle, dot eyes, polyline mouth; no glyphs.
### Task 4: Meals and groceries
- `Meals` (`meals`, value_added/value_added, 1 page; the catalog gives no repetition). `layout(rows) -> MealsLayout(day_rows, grocery_rows, grocery_cols)`: planner takes 60% of rows (1 label row + 7 days of 1..4 baselines), groceries get the rest after gap + label rows; 2 columns when rows >= 30 (a5, letter), 1 on b6.
### Task 5: Gratitude journal
- `Gratitude(count=1)` (`gratitude`, value_added/value_added; catalog's 4 is the value score, no repetition, so `count=N` like Todo, negatives rejected). `layout(rows) -> GratitudeLayout(lines, last_lines)`: fixed rows = date + 5 labels + 4 gaps; rest split evenly per block (min 1), remainder to the final "intention" block.
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
