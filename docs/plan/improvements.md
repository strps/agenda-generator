# Suggested Improvements to the Plan

Review of [plan_script_agenda.md](plan_script_agenda.md). Ordered roughly by impact.

## 1. Correctness issues (fix before coding)

### 1.1 Spreads must start on a left-hand page
The weekly planner (WO2P) is a two-page spread: Mon–Wed on the left, Thu–Sun on the right. If the page before it ends on an odd count, the spread breaks across a page turn. The same applies to a 2-page yearly or monthly.

**Fix:** add a `starts_on: left | right | any` attribute to `BasePage`. The assembler inserts a filler page (notes) when the next page would land on the wrong side. Section 5.4 already assumes odd = right, even = left, so the assembler has all it needs.

### 1.2 Imposition requires folded booklets — *resolved*
Booklets are now folded by default (5 sheets = 20 pages). Validation still applies: `imposition: true` with `folded: false` is rejected, and when `unit: pages` is used with folded booklets the count must be a multiple of 4.

### 1.3 Weeks vs. months
- Some years have **53 ISO weeks** (2026 is one), so "x52" is wrong. Derive the count from the calendar.
- A week that spans two months (e.g. Mar 30 – Apr 5) needs a placement rule for the `[monthly + weeklies per month]` ordering. Suggested rule: a week belongs to the month of its first day (or its Thursday, matching ISO).
- The first week may start in the previous year. Decide whether to include it (most commercial planners do).

### 1.4 Padding position
Padding pages must go **before** the back cover, not after it. If the cover/back cover are printed separately on card stock (common), exclude them from the booklet count entirely: add a `separate_covers: true|false` option.

### 1.5 Emojis will not render
Section 9 suggests emojis for the mood tracker. Color emoji fonts do not render reliably in print PDFs. Draw simple shapes (circles/faces) instead, or use small SVG icons via fpdf2's `image()`.

## 2. Architecture

### 2.1 Build a page plan before drawing
*Now required:* the GUI's section bar and live preview depend on it (see [gui.md](../architecture/gui.md)).

Split step 7 into two passes:
1. The assembler produces a `PagePlan`: an ordered list of `(page_class, ctx, page_number, side, booklet_index)`.
2. The exporter draws from the plan.

This makes booklet math, left/right placement, a table of contents, internal hyperlinks and a `--dry-run` summary trivial, and it is easy to unit test without rendering any PDF.

### 2.2 Write all code identifiers in English
Translatable strings (month names, labels) go in a small i18n dictionary keyed by `language`. Avoid Python's `locale` module for month names because it depends on what is installed on the system. Only user-facing text is localized.

### 2.3 `pyproject.toml` instead of `requirements.txt`
Package it with a console entry point (`agenda-gen`) so it can be installed with `pipx` or `uv tool install`. Swap `main.py` for `agenda/__main__.py`.

### 2.4 Configuration precedence
Use a single pydantic model. Load YAML into a dict, overlay the CLI options that were explicitly set, and validate once. With `typer`, the CLI and the model stay in sync.

### 2.5 Avoid the module name `calendar.py`
It shadows the standard-library `calendar` module, which the date code will probably want to use. Rename it to `dates.py`.

## 3. Printing details

- **Imposition sizes:** 2× half letter fits exactly on landscape letter, and 2× A5 on landscape A4. Other sizes (B6, custom) need scaling or centering plus crop marks. Specify this.
- **Bleed:** with `crop_marks`, the page box must grow by the bleed (usually 3 mm), and full-bleed elements (cover colors, tabs) must extend into it. Add a `bleed` parameter.
- **Creep:** in thick folded booklets, the inner pages stick out after folding. With 5 sheets this is negligible. Add a note, or an optional `creep_mm` shift if larger booklets are allowed.
- **Page count warning:** daily pages (x365) push the agenda past 400 pages. Show the total, sheet count and booklet count in the summary, and warn above a threshold.
- **Page numbers:** add optional page numbers in the outer corner. They are useful for the contents page and for checking imposition.

## 4. Product

- **Use the value score:** the `added_value` score (1–5) is defined but never used. Use it to sort the interactive menu and to define presets (`--preset essential|complete|premium`), which is more convenient than listing IDs.
- **Digital version early:** fpdf2 supports bookmarks (`start_section`) and internal links (`add_link` / `set_link`). With a `PagePlan`, a hyperlinked PDF for tablets (GoodNotes, etc.) costs little and is a strong selling point. Consider moving it from "future" into phase 7–8.
- **Localized holidays:** the `holidays` library accepts a `language` parameter, so holiday names can follow `language`.
- **Fonts:** bundle one open-source TTF family (e.g. Inter or Source Sans) under `assets/fonts/` and embed it. This gives consistent rendering and full accent support.

## 5. Testing

- **Snapshot tests:** render selected pages to PNG (`pdftoppm`) and compare them against stored references to catch layout regressions.
- **Property tests for imposition:** for any valid N, every page appears exactly once, and the front and back of each sheet sum correctly (each pair sums to N+1). `hypothesis` makes this cheap.
- **PagePlan tests:** spreads on even pages, padding count, 53-week years, week start on Sunday vs. Monday.

## 6. Phase order

Phase 4 (booklets) and the `PagePlan` should come **before** Phase 3 (core pages), right after the foundation. Placement rules affect how pages are designed, and getting them right early avoids rework. Suggested order: 1 → 2 → 4 → 3 → 7 → 8 → 5 → 6 → 9. This gives you a printable, correctly bound core agenda before you invest in the optional pages.
