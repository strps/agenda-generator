# Phase 1 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` (`.venv` is gitignored; already created, editable install, so code changes apply immediately).
- Run: `.venv/bin/agenda-gen ...` or `.venv/bin/python -m agenda ...`.
- Tests: `.venv/bin/pytest` (tests in `tests/`, `testpaths` set in pyproject).
- Lint: `.venv/bin/ruff check .` (line length 100, py311+, Python 3.13 locally).
- Layout: package `agenda/` at repo root (not `agenda_gen/`); setuptools discovers `agenda*`.
- CLI uses stdlib `argparse` (not typer); entry is `agenda.__main__:main(argv=None) -> int`.
- Deps (core): fpdf2, pydantic, PyYAML, holidays, pypdf, qrcode, Pillow. Extras: `gui` (PySide6, pypdfium2), `dev` (pytest, ruff).
- Fonts: top-level `assets/fonts/`; Inter registered by `new_document` (see Task 6).

## Log

### Tasks 1-2: pyproject, layout
- `agenda/__main__.py`: `build_parser()`, `main(argv) -> int`. Stub modules exist for everything in plan §4 plus `i18n`, `pages/{base,core,optional,value_added}`; fill in place. `tests/test_smoke.py` `MODULES` lists them; add new modules there.
- Fonts: top-level `assets/fonts/` (+ `assets/icons/`), resolve via `Path(__file__).resolve().parents[1] / "assets" / "fonts"`. A wheel would not ship them (revisit when packaging).
- Gotcha: `agenda/calendar.py` shadows stdlib only for relative imports; use `from agenda import calendar`, never run scripts from inside `agenda/`.

### Task 3: config model
- `agenda/config.py`: `Config(BaseModel)` (extra="forbid", validate_assignment). All plan §2 params plus amendments: `bleed` (3 mm), `separate_covers`, `creep_mm`, `preset`, `page_numbers`, `debug_grid`. Property `pages_per_booklet`. Tests in `tests/test_config.py`.
- `page_size` stays a raw normalized `str` (lowercased name, or custom "WxH" as typed); `orientation` separate.
- `daily_months` accepts `"1-3,6"` or a list; stored as sorted unique ints. `year` defaults to the current year. `pages=None` means "all core pages" (catalog resolves it). `num_booklets: int | "auto"`.
- Model validators: `imposition` needs `booklet_folded`; folded + unit=pages needs size % 4 == 0.
- Not done (later phases): YAML loading, CLI overlay, presets expansion, margin-vs-page-size checks.

### Task 4: sizes
- `agenda/sizes.py`: `SIZES` (portrait mm, five names), `PageSize(width, height)` NamedTuple, `parse_size(spec)` (name case-insensitive or `WxH`, each side 50-1000 mm, else ValueError), `resolve_size(spec, orientation)`.
- Decision: orientation normalizes: portrait => width <= height, landscape => width >= height (so custom `200x100` portrait gives 100x200).
- `Config.page_size` validator now calls `parse_size`; new property `Config.page_dimensions` -> final (w, h) mm. Use that for `FPDF(unit="mm", format=cfg.page_dimensions)` (next task).
- Tests: `tests/test_sizes.py`.

### Task 5: fpdf2 document
- `agenda/exporter.py`: `new_document(cfg) -> FPDF` (mm, `format=cfg.page_dimensions`, auto page break off, margins 0, title/creator/author set), `add_blank_pages(pdf, n)`, `write_pdf(pdf, path=DEFAULT_OUTPUT)` (creates parent dirs), `export_blank(cfg, pages, path)`. `DEFAULT_OUTPUT = output/agenda.pdf` (`output/` is created on demand).
- CLI temporary flags: `-o/--output`, `--pages` (default 4), `--page-size`, `--orientation`; builds `Config(**overrides)`, exit 2 on invalid config. Replace with the real CLI/config overlay later.
- Page size verified via pypdf mediabox (pt / (72/25.4)) in `tests/test_exporter.py`.
- Note: fpdf2 margins set to 0 on purpose; the margins/grid tasks own real margins (alternating inner/outer by page side).

### Task 6: fonts
- Bundled Inter 4.0 static TTFs (OFL, `assets/fonts/Inter-LICENSE.txt`): Regular, Bold, Italic, BoldItalic (~1.6 MB). Docs (improvements.md) suggested Inter.
- `agenda/exporter.py`: `FONT_DIR`, `FONT_FAMILY = "Inter"`, `FONT_FILES` (style -> file), `register_fonts(pdf, font_dir)`, `FontsMissingError` (lists missing files + dir). `new_document(cfg, font_dir=FONT_DIR)` calls it.
- Use `pdf.set_font("Inter", "", 10)`; styles `""`, `"B"`, `"I"`, `"BI"`. Any other weight needs a new file added to `FONT_FILES`.
- CLI prints the error to stderr and returns exit code 1 (2 stays for invalid config).
- Tests in `tests/test_exporter.py` (accent text extracted from PDF, missing-dir error, CLI exit code).
- Gotcha: fpdf2 `cell()` defaults to staying on the line; pass `new_x="LMARGIN", new_y="NEXT"` for line breaks (margins are 0).
