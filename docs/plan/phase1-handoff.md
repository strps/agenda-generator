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
- Fonts: top-level `assets/fonts/` (decided, task 2); see Task 2 log.

## Log

### Task 1: pyproject + entry point
- Built `pyproject.toml`, `.gitignore`, `agenda/__init__.py` (`__version__`), `agenda/__main__.py` (`build_parser()`, `main(argv)`; only `--version` so far, prints "not implemented yet").
- Later tasks extend `build_parser()`/`main()`; keep `main` returning an int exit code.

### Task 2: package layout
- Created stub modules (one-line docstring each) under `agenda/`: config, sizes, catalog, calendar, grid, tokens, draw, themes, assembler, imposition, exporter, i18n (not in plan §4, added for the i18n task), and `agenda/pages/{base,core,optional,value_added}.py`. Fill them in place; do not rename.
- `tests/test_smoke.py` imports every module; when adding a module, add it to `MODULES`.
- Decision: fonts stay in top-level `assets/fonts/` (plus `assets/icons/`), with `.gitkeep` placeholders; no package-data. Resolve with `Path(__file__).resolve().parents[1] / "assets" / "fonts"`. Works for the editable install; a built wheel would not ship them (revisit before packaging; then move into `agenda/assets` and add `[tool.setuptools.package-data]`).
- Gotcha: `agenda/calendar.py` shadows stdlib only for relative imports inside the package; always use `from agenda import calendar` / absolute imports, never run scripts from inside `agenda/`.
- No `main.py`/`config.yaml`/`output/` from plan §4 yet: entry is `agenda.__main__`.

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
