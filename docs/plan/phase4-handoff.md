# Phase 4 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as before (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Plan types live in `agenda/assembler.py`; unit tests build entries by hand (`tests/test_assembler.py`), no rendering.

## Log

### Task 1: PlanEntry / PagePlan
- `PlanEntry` (frozen, `eq=False`, so not hashable by value): `page_class, ctx, page_number, side, booklet_index, section, page_in_instance=0, kind="page"|"filler"|"padding"`. Build with `make_entry(...)` (side from `grid.side_for_page`).
- Spread = 2 entries sharing the same ctx object (`page_in_instance` 0/1); drawer calls `draw` only when `entry.starts_instance`.
- Blank filler: `page_class=None`, `kind="filler"`, section of the page it precedes. Padding: `kind="padding"`, real class (e.g. `Notes`) or None.
- `booklet_index` is 1-based, set by `build_plan` (None only for hand-built entries).
- `PagePlan(entries)` frozen tuple; validates `page_number == i+1` and side. Helpers: `len`, iter, `[i]`, `page_count`, `by_section`, `by_booklet`, `drawn()`, `sections()` (runs `(section, first, last)`).

### Task 2: build_plan ordering
- `build_plan(config) -> PagePlan` in assembler.py; inner `put(cls, ctx)` appends `cls.pages` entries ; another hook before back matter for padding (task 5).
- Mirrors `export_agenda` (still the renderer). Front: Cover, PersonalInfo, Yearly; back: Notes, Contacts, BackCover.
- Optional/value-added: classes from catalog (by category order) whose id is in `config.pages`; `pages=None` means none (core only). Each class's `instances(config)` in order.
- Tests: tests/test_build_plan.py (default, weekly-only, daily-only, year edges).

### Task 3: starts_on fillers
- `put` inserts one filler (`page_class=None`, `kind="filler"`, ctx `{}`, section of the class it precedes) when `side_for_page(next) != cls.starts_on`; same rule as `export_agenda`. Only Weekly (`left`) uses it today.
- Fillers sit before the instance's first entry, so padding (task 5) and booklet math must count them as ordinary pages.
- Tests replay the rule independently (`_reference_fillers`), no rendering.

### Task 4: booklet math
- assembler.py: `pages_per_sheet(folded)`, `pages_per_booklet(size, unit, folded)` (mirrors `Config.pages_per_booklet`), `booklet_index_for(page, per)`, `plan_booklets(total, per, num_booklets="auto") -> BookletLayout(total_pages, pages_per_booklet, count, padding, overflow)`.
- Fixed int `num_booklets`: count = N, padding = N*per - total; if too few, `overflow` > 0, padding 0 (no truncation; validation/summary decide). 0 pages auto = 1 booklet.
- `build_plan` sets `booklet_index` from config only; it does not use `num_booklets` or call `plan_booklets` (task 5 should, to get padding). Odd inputs (folded pages not multiple of 4) are not checked here.
- Tests: tests/test_booklets.py.
