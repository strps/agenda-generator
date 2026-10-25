# Phase 8 handoff

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- Imposition is a post-processing step on the finished PDF; the normal export path stays byte-identical.
- Pure logic (ordering, placement math) is Qt-free with unit tests; rules live in `Config` only.
- `Config` already has `imposition` (requires `booklet_folded`) and `crop_marks`; CLI has `--imposition`.

## Log
- T1 `agenda.imposition.imposition_order(n)` -> list of `(left, right)` 1-based pages per sheet side (front, back per sheet); ValueError unless n % 4 == 0. Tests `tests/test_imposition.py` (incl. agreement with `preview_model.sheet_rows`). Per-booklet only: the caller maps booklet page k to plan index and handles padding to a multiple of 4.
- T2 `imposition`: `place_two_up(pw,ph,sw,sh)` -> (scale<=1, left_origin, right_origin) y-up, each page centred in its half; `choose_sheet` (letter vs A4 landscape, bigger scale, letter on tie); `impose_pages(reader, sides, sheet_mm=None, writer=None)` (1-based pages, None = blank half); `impose_booklets(pdf_bytes, booklet_of)` pads each booklet to x4 with blanks, pages with booklet_index None (separate covers) stay 1-up before/after. `export_agenda` calls it when `cfg.imposition`; else unchanged. T3 (bleed/marks) hooks into `impose_pages` (sheet drawing) and `place_two_up`.
