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
- `booklet_index` is None until the booklet task (then 1-based).
- `PagePlan(entries)` frozen tuple; validates `page_number == i+1` and side. Helpers: `len`, iter, `[i]`, `page_count`, `by_section`, `by_booklet`, `drawn()`, `sections()` (runs `(section, first, last)`).

### Task 2: build_plan ordering
- `build_plan(config) -> PagePlan` in assembler.py; inner `put(cls, ctx)` appends `cls.pages` entries (hook comment for starts_on fillers, task 3); another hook before back matter for padding (task 5).
- Mirrors `export_agenda` (still the renderer). Front: Cover, PersonalInfo, Yearly; back: Notes, Contacts, BackCover.
- Optional/value-added: classes from catalog (by category order) whose id is in `config.pages`; `pages=None` means none (core only). Each class's `instances(config)` in order.
- Tests: tests/test_build_plan.py (default, weekly-only, daily-only, year edges).
