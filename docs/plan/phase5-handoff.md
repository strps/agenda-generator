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

### Task 1: Goals
- `Goals` (`goals`, optional/optional, 1 page): `Goals.layout(rows) -> (goals, steps)`: 6 goals, else 5, with up to 4 steps, min 2; block = title + steps + deadline + 1 gap row.
- Keys `goals.title/goal/step/deadline` (`goals.step` unused so far). Plan test: after dailies, before Notes.

### Task 2: Important dates
- `ImportantDates` (`important_dates`, optional/optional, 1 page): `layout(rows) -> entries` = `max(1, rows // 6 - 2)`; 12 month blocks (2 cols x 6 rows: title row, entries, gap row), each entry a short day rule + name rule.
- Month names via `Strings.month_name(m)`; key `dates.title` only.

### Task 3: To-do list
- `Todo(count=1)` (`todo`, optional/optional): `count` -> `instances()` N pages (negative raises), like Notes. No config field for count exists (Notes has none), so `config.pages` gives 1.
- `Todo.layout(rows) -> rows - 1` task rows (row 1 = labels); 1 column on all sizes; due rule = last grid column. Keys `todo.title/task/due`.
