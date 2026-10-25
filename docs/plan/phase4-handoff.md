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

### Tasks 2-3: build_plan
- `build_plan(config) -> PagePlan`; `put(cls, ctx)` appends `cls.pages` entries (spread = shared ctx). Mirrors `export_agenda` (still the renderer): Cover, PersonalInfo, Yearly; per month/week; extras (`config.pages` ids, catalog order; None = core only); Notes, Contacts, BackCover.
- One blank filler (`page_class=None`, `kind="filler"`) before an instance whose `starts_on` side mismatches; fillers count as pages in booklet math.
- Tests: tests/test_build_plan.py (fillers replayed independently).

### Task 4: booklet math
- `pages_per_sheet`, `pages_per_booklet`, `booklet_index_for`, `plan_booklets(total, per, num_booklets) -> BookletLayout(..., padding, overflow)`; too-small fixed count: `overflow` > 0, padding 0.

### Task 5: padding
- `Config.pad_with` (default "notes", validated against catalog). Padding goes before BackCover: tries 0,1,2.. pad units until `plan_booklets` fits; `kind="padding"`. No whole-unit fit: blank padding (`page_class=None`, section `front_back`). Fixed `num_booklets` too small: no padding, plan overflows. Tests: tests/test_padding.py.

### Task 6: separate_covers
- True: Cover = page 1, blank inside-cover filler = page 2, ..., blank inside-back filler, BackCover last. All four stay in the plan (drawn/shown) with `booklet_index=None`; inner block (pages 3..N-2) starts on a right page, is padded and indexed alone (`booklet_index_for(page-2, per)`), so inner count is a multiple of per. Sides/page numbers stay global (Cover recto, back cover verso). Default False unchanged.
- Tests at the end of tests/test_padding.py. Summary/validation should count covers separately.

### Task 7: daily_months
- Filter lives in `build_plan` (`d.month in config.daily_months`); `Daily.instances` unchanged. Weeks/months unaffected; later steps (fillers, padding, booklets) derive from the filtered list. Tests: tests/test_daily_months.py.
- Gotcha: a year's first/last days in an ISO week owned by the neighbouring year have no Daily (2028 gives 364 dailies), independent of daily_months.

### Task 8: validation
- `Config._check_booklet_rules` (model_validator): imposition needs folded; `unit="pages"` size must be a multiple of 4 (folded) or 2 (flat; decision). Sheets always valid. Tests in tests/test_config.py.
- `build_plan` asserts the counted block is a multiple of 4 when folded and not overflowing.
- Overflow (fixed `num_booklets` too small) is NOT an error: plan builds, `BookletLayout.overflow` > 0. Task 9 summary must warn.
- Gotcha: pydantic `validate_assignment` raises but leaves the bad value set; don't rely on rollback.

### Task 9: summary
- `summarize(plan, config) -> PlanSummary` (frozen, pure, not stored on PagePlan; `.format()`/`str()` multi-line text). Fields: total/counted/cover pages, fillers, padding_pages, blank_padding, pages_per_booklet, booklets, sheets_per_booklet, total_sheets, overflow, warnings.
- Counted pages = entries with `booklet_index` (separate_covers); covers not turned into sheets. Warnings: overflow, `LARGE_PAGE_COUNT`=600 (suggests daily_months), blank padding. Tests: tests/test_summary.py.
