# Phase Tracker

Progress tracker for the [development plan](plan_script_agenda.md). Update the status table and tick tasks as work lands.

**Status values:** `Not started` · `In progress` · `Blocked` · `Done`

## Overview

| Phase | Status | Estimate | Started | Finished | Depends on | Notes |
|---|---|---|---|---|---|---|
| 1. Foundation | Done | 1–2 days | 2026-10-25 | 2026-10-25 | — | |
| 2. Calendar | Done | 1 day | 2026-10-25 | 2026-10-25 | 1 | |
| 3. Core pages | Done | 3–4 days | 2026-10-25 | 2026-10-25 | 1, 2, 4 | |
| 4. Booklets & page plan | Done | 1–2 days | 2026-10-25 | 2026-10-25 | 1, 2 | |
| 5. Optional pages | Done | 3 days | 2026-10-25 | 2026-10-25 | 3 | |
| 6. Value-added pages | In progress | 4 days | 2026-10-25 | | 3 | |
| 7. CLI & YAML | Not started | 1 day | | | 1, 4 | |
| 7b. GUI | Not started | 4–5 days | | | 3, 4, 7 | |
| 8. Imposition | Not started | 2 days | | | 4 | |
| 9. Testing & polish | Not started | 2–3 days | | | all | |

**Recommended execution order:** 1 → 2 → 4 → 3 → 7 → 8 → 7b → 5 → 6 → 9. The booklet logic and page plan come before the core pages because page placement (left/right, spreads) affects page design. See [improvements.md §6](improvements.md#6-phase-order).

---

## Phase 1 — Foundation

**Goal:** an installable project that produces a blank, correctly sized PDF with alternating margins.

- [x] `pyproject.toml` with `agenda-gen` console entry point; `agenda/__main__.py`
- [x] Package layout as in [plan §4](plan_script_agenda.md#4-project-architecture)
- [x] Config model (pydantic) with all parameters and defaults ([plan §2](plan_script_agenda.md#2-configuration-parameters))
- [x] `sizes.py`: named sizes + custom `WxH` in mm, orientation
- [x] fpdf2 document in mm (`FPDF(unit="mm", format=...)`)
- [x] Bundle and register TTF fonts in `assets/fonts/`; fail if missing
- [x] `tokens.py` and `grid.py`: margins, 6 columns, 5 mm baseline ([layout-grid.md](../architecture/layout-grid.md))
- [x] Alternating inner/outer margins by page side
- [x] `--debug-grid` overlay (margins, columns, baseline, mm rulers)
- [x] i18n string table (`es`, `en`)

**Done when:** `agenda-gen --debug-grid` outputs a few half-letter pages whose grid overlay shows margins swapping between left and right pages.

## Phase 2 — Calendar

**Goal:** all date logic, independent of drawing.

- [x] Months, days and month grids for any year; `week_start` monday/sunday
- [x] ISO weeks, including 52/53-week years; first week overlapping the previous year
- [x] Rule for weeks spanning two months (week belongs to the month of its first day)
- [x] Holidays via `holidays` (default `CR`), names localized by `language`
- [x] Unit tests: leap years, 53-week years, Sunday start

**Done when:** tests pass for 2026 (53 weeks), 2027 and 2028 (leap year).

## Phase 3 — Core pages

**Goal:** a complete, usable agenda with the core pages.

- [x] `BasePage` with `id`, `name`, `category`, `section`, `pages`, `starts_on`, `instances()`, `draw()`
- [x] `@register` catalog
- [x] Cover
- [x] Personal information
- [x] Yearly calendar
- [x] Monthly planner
- [x] Weekly planner (WO2P spread, always starting on a left page)
- [x] Daily planner
- [x] Notes (lined, dotted, grid, blank)
- [x] Contacts
- [x] Back cover
- [x] Holidays and weekends marked on calendar pages

**Done when:** the default config produces a full agenda where every page stays inside the safe area and weekly spreads face each other.

## Phase 4 — Booklets & page plan

**Goal:** the ordered `PagePlan` that drives drawing, the GUI and imposition.

- [x] `PagePlan` entries: `(page_class, ctx, page_number, side, booklet_index, section)`
- [x] Ordering: front matter → per month: monthly, then per week: weekly spread → that week's dailies → optional → value-added → back matter
- [x] `starts_on` handling: insert filler when a spread would start on the wrong side
- [x] Booklet math, folded (default, 4 pages/sheet) and flat (2 pages/sheet); `sheets`/`pages` units
- [x] Padding with `pad_with` pages, placed before the back cover
- [x] `separate_covers` option
- [x] `daily_months` filter
- [x] Validation: imposition requires folded; folded page counts multiple of 4
- [x] Summary: pages, sheets, booklets, padding, page-count warning
- [x] Unit tests for the plan (no rendering)

**Done when:** `build_plan(config)` returns a correct plan for the default config and edge cases (1 page, 1-sheet booklets, weekly-only, daily-only).

## Phase 5 — Optional pages

- [x] Yearly goals
- [x] Important dates
- [x] To-do list
- [x] Projects
- [x] Budget (x12)
- [x] Habit tracker (x12)
- [x] Monthly review (x12)
- [x] Schedule
- [x] Holidays list
- [x] Passwords (with warning)

**Done when:** each page renders at every supported size within the safe area.

## Phase 6 — Value-added pages

- [x] Monthly quotes
- [x] Vision board
- [x] Health tracker (drawn mood shapes, no emoji)
- [x] Meals and groceries
- [x] Gratitude journal
- [x] Books, movies and series
- [x] Travel planner
- [x] 30-day challenges
- [x] Idea map
- [x] QR codes from user URLs
- [x] Physical extras guide
- [x] Niche packs (entrepreneur, student, fitness)
- [ ] Presets by value score (`--preset essential|complete|premium`)

**Done when:** each page renders at every supported size, and presets select the expected pages.

## Phase 7 — CLI & YAML

- [ ] `typer` CLI mirroring the config model
- [ ] YAML loading; CLI overrides YAML; single validation pass
- [ ] `--list` catalog with value scores
- [ ] `--dry-run` prints the plan summary without rendering
- [ ] Sample `config.yaml`

**Done when:** every example in [plan §8.1](plan_script_agenda.md#81-command-line) runs.

## Phase 7b — GUI

Spec: [gui.md](../architecture/gui.md).

- [ ] PySide6 main window and layout
- [ ] Settings panel generated from the config model; open/save YAML
- [ ] `render_pages(config, plan, indices)` in the core
- [ ] Preview: single, spread and sheet modes; zoom; pypdfium2 rasterising
- [ ] Background worker + cache keyed by config hash, page, zoom; 300 ms debounce
- [ ] Section bar: proportional segments, 2 px section gaps, padding hatch, booklet ticks, position marker
- [ ] Section colors for light and dark mode as specified
- [ ] Bar interaction: hover tooltip, click/drag navigation, keyboard, legend click
- [ ] Legend with counts + summary line
- [ ] Export with progress bar

**Done when:** changing any setting updates the bar instantly and the preview within ~1 s, and export produces the same PDF as the CLI.

## Phase 8 — Imposition

- [ ] `imposition_order(n)` for folded booklets
- [ ] 2-up placement on landscape letter/A4 with pypdf; scaling/centering for other sizes
- [ ] Bleed and crop marks
- [ ] Property tests: every page once; each sheet side's pair sums to N+1

**Done when:** a printed, folded test booklet reads in order with the binding margin on the fold side.

## Phase 9 — Testing & polish

- [ ] Snapshot tests (pages → PNG via `pdftoppm`)
- [ ] Real print test at half letter and A5
- [ ] Themes (at least 2)
- [ ] Hyperlinked digital version (bookmarks, month/week links)
- [ ] Page numbers (optional)
- [ ] README and user guide in `docs/guides/`

**Done when:** a full printed agenda passes review with no layout or ordering defects.

---

## Change log

| Date | Change |
|---|---|
| 2026-10-25 | Tracker created. Decisions so far: folded booklets by default (selectable), weekly + daily planners, `CR` holidays, fpdf2 rendering, PySide6 GUI with section bar. |
| 2026-10-25 | Phase 1 done: package, config, sizes, fonts, grid, alternating margins, `--debug-grid`, i18n table (`es`, `en`). |
| 2026-10-25 | Phase 2 done: `agenda/calendar.py` (months, month grids, ISO weeks, weeks by month, localized holidays) with tests for 2026 (53 weeks), 2027, 2028 (leap), Monday/Sunday start. |
