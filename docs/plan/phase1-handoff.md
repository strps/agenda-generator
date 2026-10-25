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
- Fonts: plan puts them in top-level `assets/fonts/`. Undecided whether to move them into the package; if so, add `[tool.setuptools.package-data]` to pyproject.

## Log

### Task 1: pyproject + entry point
- Built `pyproject.toml`, `.gitignore`, `agenda/__init__.py` (`__version__`), `agenda/__main__.py` (`build_parser()`, `main(argv)`; only `--version` so far, prints "not implemented yet").
- Later tasks extend `build_parser()`/`main()`; keep `main` returning an int exit code.
- Gotcha: no `tests/` dir yet; `pytest` exits 5 until a test exists. Installed packages' new subpackages are picked up automatically (editable).
