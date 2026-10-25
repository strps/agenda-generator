# Phase 6 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Value-added pages live in `agenda/pages/value_added.py`, subclass `BasePage`, use `@register`, category and section `value_added`; ids come from plan §3.3. They appear in the plan only when listed in `config.pages`.
- `draw(pdf, ctx, config, grids)`: `grids[0]` is the page's `Grid`; never hardcode mm (use `g.header/content/safe/rows/row(n)/baseline`, `tokens`).
- Header: `pdf.c_margin = 0`, Inter bold `TYPE_SIZES_PT[3]` accent in `g.header`; strings via `Strings(config.language)("key", n=...)`, keys in both es and en in `agenda/i18n.py`.
- x12 pages: `instances` returns `month_ctxs(config)`. Helpers in `agenda/draw.py`: `draw_checkbox`, `draw_circle`, `draw_label_rule`, `draw_pattern`.
- Tests: `from helpers import render_page, assert_in_safe_area, drawn_points`; no emoji, draw shapes. See `tests/test_monthly_quotes.py`.
- Phase 5 open items: see the wrap-up in `phase5-handoff.md`.

## Log
### Task 1: Monthly quotes
- `MonthlyQuotes` (`quotes`, value_added/value_added, 1 page x12 via `month_ctxs`); `layout(rows) -> (quote rows, reflection rules)`: quote area = half the rows in whole 2-baseline lines, label row + rules below.
- Quotes are i18n keys `quotes.1..12` (es, en) plus `quotes.title/reflection`. Rule: original sayings, no attribution; name an author only for a certain public-domain quote (none now).
- Wrapping: `pdf.multi_cell(..., dry_run=True, output="LINES")`; tries `QUOTE_SIZES`, drops lines that don't fit.
