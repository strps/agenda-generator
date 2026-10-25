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
