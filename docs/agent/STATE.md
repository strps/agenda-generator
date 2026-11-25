# STATE: agenda-generator        (working memory of the active plan, rewritten each phase, max 40 lines)
Plan: 2026-11-25-text-fit-warnings
Last phase: 01
ADRs: docs/adr/README.md (long-lived decisions; read the index, open an ADR only when your phase touches it)

## Decisions (this plan)
- fit_text's `width_of(text)` measures at `size_pt` only; widths are scaled linearly by size/size_pt for shrink/wrap, so callers pass a one-arg measurer: keeps fake test measurers trivial and fpdf out of the module (text-fit-warnings/01)
- wrap: size = largest in [min_scale, 1]*size_pt (0.25 pt steps) where max_lines lines fit `height`, else the minimum; line count capped by height at that size; last line is day_extras.truncate of the remainder (text-fit-warnings/01)
- Text that fits on one line at size_pt returns unchanged in every mode (text-fit-warnings/01)

## Contracts (between this plan's phases)
- Fitting: agenda/textfit.py::fit_text -> FitResult(lines, size_pt, cut); FIT_MODES, FOOTER_FIT_MODES
- Cut collection: agenda/textfit.py::CutLog (add(page, region, text), entries, pages(region), bool, len); format_ranges(pages) -> "3, 5, 14-20"
- Region ids: "header", "footer"

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- none
