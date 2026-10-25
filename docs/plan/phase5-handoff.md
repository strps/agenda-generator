# Phase 5 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Optional pages live in `agenda/pages/optional.py`, subclass `BasePage`, use `@register`; they appear in the plan only when listed in `config.pages`.
- `draw(pdf, ctx, config, grids)`: caller adds pages; `grids[0]` is the page's `Grid`; never hardcode mm (use `g.header/content/safe/rows/row(n)/baseline`, `tokens`).
- Header: `pdf.c_margin = 0`, Inter bold `TYPE_SIZES_PT[3]` accent in `g.header`; strings via `Strings(config.language)("key", n=...)`, keys in both es and en in `agenda/i18n.py`.
- Shared helpers in `agenda/draw.py`: `draw_pattern`, `draw_checkbox(pdf, x, y, size)`, `draw_label_rule(pdf, x, w, y, label, label_w)` (label cell above baseline `y`, rule on `y`).
- Tests: `from helpers import render_page, assert_in_safe_area, drawn_points`; no emoji, draw shapes.

## Log

### Task 2: Important dates
- `ImportantDates` (`important_dates`, optional/optional, 1 page): `layout(rows) -> entries` = `max(1, rows // 6 - 2)`; 12 month blocks (2 cols x 6 rows: title row, entries, gap row), each entry a short day rule + name rule.

### Task 3: To-do list
- `Todo(count=1)` (`todo`, optional/optional): `count` -> `instances()` N pages (negative raises), like Notes. No config field for count exists (Notes has none), so `config.pages` gives 1.
- `Todo.layout(rows) -> rows - 1` task rows (row 1 = labels); 1 column on all sizes; due rule = last grid column. Keys `todo.title/task/due`.

### Task 4: Projects
- `Projects(count=1)` (`projects`): rows = 3 field rows (name, objective, start|deadline halves), gap, task labels, tasks, gap, notes label, notes rules.
- `Projects.layout(rows) -> (tasks, notes)`: `FIXED_ROWS`=7; notes = max(2, free//3) (capped at free), tasks = rest.
- Shared `_draw_task_list(pdf, g, row, n, labels, box, due_cols)` in optional.py (label row + n checkbox rows); Todo uses it too.
- Keys `projects.title/name/objective/start/deadline/task/due/notes`.

### Task 5: Budget
- `Budget` (`budget`, optional/optional, 1 page x12): `Budget.layout(rows) -> (income, fixed, variable, savings)` write-in rows; `FIXED_ROWS`=11, rest split by `WEIGHTS` (1,2,2,1). Amount = last 2 grid cols.
- Shared `month_ctxs(config)` in `agenda/pages/base.py` -> `[{"month", "year"}]*12`.
- Keys `budget.*` (title takes `{month} {year}`).

### Task 6: Habits
- `Habits` (`habits`, optional/optional, 1 page x12 via `month_ctxs`): `layout(rows) -> habits` = `rows - 2` (title row 0, day numbers row 1), cap `MAX_HABITS`=20. Name column = first `NAME_COLS`=2 grid columns; days share the rest (cell ~2.1 mm on b6, 31 days).
- New shared `draw_circle(pdf, cx, cy, d)` in draw.py (monthly review rating can reuse). Weekend columns use `weekend_fill`.
- Day numbers use Inter regular 6pt (bold overlaps on b6). Keys `habits.title/habit`. Circle test counts bezier `c` ops / 4.

### Task 7: Monthly review
- `MonthlyReview` (`monthly_review`, optional/optional, 1 page x12 via `month_ctxs`): `layout(rows) -> (wins, challenges, lessons, goals)` write-in rows; `FIXED_ROWS`=9, rest split equally, leftovers to first sections. Goals rows have checkboxes (side = 0.6 baseline).
- Last row: label + 5 `draw_circle`s right-aligned (pitch 2 baselines). Keys `review.*`.

### Task 8: Schedule
- `Schedule` (`schedule`, optional/optional, 1 page): 7 weekday columns (short names, `config.week_start` order, weekend tint) all sizes; hour label column = half a grid column. Key `schedule.title`.
- `Schedule.layout(rows) -> (hours, baselines per hour)`: tallest band of 3/2/1 rows keeping >= 10 hours, max 15 (7:00-21:00); b6 gives 13 hours x 2 rows.

### Task 9: Holidays
- `Holidays` (`holidays`, optional/optional, 1 page): `layout(rows, n) -> (cols, shown, per_col)`; cap = `rows // ROW_BASELINES`(2); n <= cap one column, else two columns showing first `min(n, 2*cap)` (truncated); n=0 or unsupported country (`ValueError` caught) => cap empty rows.
- Es dates "1 ene", en "Jan 1"; names ellipsized via `_ellipsize(pdf, text, w)`. Reuses keys `holidays.title`.

### Task 10: Passwords
- `Passwords(count=1)` (`passwords`, optional/optional): `layout(rows) -> entries` = `max(0, (rows - 6) // 2)`; `WARN_ROWS`=4 (bordered box, drawn triangle icon, wrapped text, max 3 lines, tested), 1 gap row, label row, entries of 2 rows in 3 columns. Keys `passwords.*`.

## Phase 5 wrap-up (open items for later phases)
- Done-when verified in `tests/test_optional_pages.py`: all 10 ids x es/en x all 5 registry sizes in safe area; `export_agenda` with all ids at every size matches plan page count.
- x12 pages (budget, habits, monthly review) sit after the dailies, not next to their months.
- `Todo/Projects/Passwords count` has no config field (always 1 via `config.pages`).
- `Goals.BOX` and `ImportantDates.DAY_W/DAY_GAP` are hardcoded mm; Projects.LABEL_W and Todo.BOX likewise.
- i18n keys `goals.step` and `holidays.label` are unused.
- Habits cells are ~2 mm wide on b6.
- Contacts' inline label+rule is not refactored onto `draw_label_rule`.
