# Phase 4 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Same env/commands as before (`.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`).
- Plan types live in `agenda/assembler.py`; unit tests build entries by hand (`tests/test_assembler.py`), no rendering.

## Log

### Tasks 1-3: PlanEntry / PagePlan / build_plan
- `PlanEntry` (frozen, `eq=False`): `page_class, ctx, page_number, side, booklet_index (1-based), section, page_in_instance, kind="page"|"filler"|"padding"`. `make_entry(...)` derives side.
- Spread = 2 entries sharing one ctx; draw only when `entry.starts_instance`. Blank: `page_class=None`.
- `PagePlan` (frozen tuple, validated): `page_count`, `by_section`, `by_booklet`, `drawn()`, `sections()`.
- `build_plan(config)`: Cover, PersonalInfo, Yearly; per month/week; extras (`config.pages`); Notes, Contacts, padding, BackCover. One blank filler before an instance on the wrong `starts_on` side.

### Tasks 4-6: booklets, padding, separate_covers
- `pages_per_sheet`, `pages_per_booklet`, `booklet_index_for`, `plan_booklets(...) -> BookletLayout(padding, overflow)`.
- `pad_with` padding goes before BackCover (whole units, else blank padding). Fixed `num_booklets` too small: no padding, `overflow` > 0.
- `separate_covers`: pages 1-2 and last 2 have `booklet_index=None`; inner block padded/indexed alone.

### Tasks 7-9: daily_months, validation, summary
- `daily_months` filter is in `build_plan`. `Config._check_booklet_rules`: imposition needs folded; `unit="pages"` multiple of 4 (folded) / 2 (flat). Overflow is not an error.
- `summarize(plan, config) -> PlanSummary` (pure; `.format()`); warnings: overflow, >600 pages, blank padding.

### Task 10: plan tests, orphan dailies, renderer
- Fixed: days of `config.year` in a neighbour year's ISO week now get a Daily (early ones after the January monthly, late ones after the last December week); 365/366 dailies every year, both week starts.
- `export_agenda(cfg, path)` now iterates `build_plan`; draws each instance once after adding all its pages (base.py contract: `pdf.page` is the last page of the instance).
- tests/test_plan_cases.py: `check_plan(cfg)` invariants over CASES; "1 page" = smallest plan (no planners, `pages=[]`, about 18-20 pages), since cover/monthlies/back matter are fixed.

## Phase 4 wrap-up / open items for Phase 5+

- Done when verified: default 2026 = 540 pages, 27 booklets x 5 sheets, 135 sheets; build_plan ~4 ms.
- 41 blank `starts_on` fillers in the default plan (~8%); consider Notes fillers instead.
- `validate_assignment` does not roll back a failed assignment: GUI must rebuild Config, not mutate it.
- `summarize` is not wired to the CLI yet (Phase 7 `--dry-run`). `LARGE_PAGE_COUNT = 600` is a guess.
- Optional/value-added pages appear only when listed in `config.pages` (default: none).
