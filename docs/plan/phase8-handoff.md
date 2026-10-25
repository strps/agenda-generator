# Phase 8 handoff

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Imposition is a post-processing step on the finished PDF; the normal export path stays byte-identical.
- Pure logic (ordering, placement math) is Qt-free with unit tests; rules live in `Config` only.
- `Config` has `imposition` (requires `booklet_folded`), `crop_marks` (requires `imposition`), `bleed` (mm); CLI has the flags; GUI panel auto-generates from the model.

## Log
- T1 `agenda.imposition.imposition_order(n)` -> list of `(left, right)` 1-based pages per sheet side (front, back per sheet); ValueError unless n % 4 == 0. Tests `tests/test_imposition.py` (incl. agreement with `preview_model.sheet_rows`). Per-booklet only: the caller maps booklet page k to plan index and handles padding to a multiple of 4.
- T2 `imposition`: `place_two_up(pw,ph,sw,sh)` -> (scale<=1, left_origin, right_origin) y-up, each page centred in its half; `choose_sheet` (letter vs A4 landscape, bigger scale, letter on tie); `impose_pages(reader, sides, sheet_mm=None, writer=None)` (1-based pages, None = blank half); `impose_booklets(pdf_bytes, booklet_of)` pads each booklet to x4 with blanks, pages with booklet_index None (separate covers) stay 1-up before/after. `export_agenda` calls it when `cfg.imposition`; else unchanged.
- T3 `crop_mark_segments(x,y,w,h,bleed,length)` (8 lines), `marks_inset(bleed)`, `MARK_LEN_MM=3`; `place_two_up/placement_scale/choose_sheet` take `inset` (shrinks pages to leave room for marks); `impose_pages/impose_booklets(..., bleed_mm=None)` draw marks (None = none, output unchanged). Export passes `cfg.bleed` if `cfg.crop_marks`. Source pages have no art past the trim, so bleed = gap before each mark. New rule: `crop_marks` requires `imposition`.
- T4 Property tests in `tests/test_imposition.py` (n = 4..200): every page once, pairs sum to n+1, every side is (even left, odd right) = `side_for_page`. PDF-level: each side holds the expected pages, left page left of the centre, with/without marks. Binding: real imposed export (inner 15 > outer 10) keeps content >= inner from the fold and >= outer from the sheet edge on both halves. No defects found. Physical print check is manual.
