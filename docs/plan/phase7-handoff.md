# Phase 7 handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`, `.venv/bin/agenda-gen`.
- CLI code in `agenda/cli.py` (typer); `agenda/__main__.py` only re-exports `main`.
- Rules live in `Config` only; the CLI maps flags to Config kwargs and never re-checks them.
- Tests: pure logic first, then typer `CliRunner` (`tests/test_cli.py`); one subprocess end-to-end test.

## Log
### Task 1: typer CLI
- `agenda.cli`: `app` (one command `run`), `main(argv) -> int` (wraps `app`, returns the exit code; used by the entry point and tests), `build_overrides(**flags) -> dict` (drops `None`, splits comma lists, merges `--pages` + `--category` into one de-duplicated `pages`, `--qr-url` repeatable -> `qr_urls`, `num_booklets` digits -> int), `split_csv`.
- Every Config field has a flag (underscores -> dashes); aliases `--size`, `--booklet`, `--unit`; bools are `--folded/--flat` and `--x/--no-x`. Unset flags stay `None`, so a later YAML layer can sit under them.
- `--pages` now means catalog ids (plan §8.1); the old blank-page option is `--blank-pages N`. Validation errors: stderr `agenda-gen: ...`, exit 2; missing fonts exit 1.
- Unknown ids in `--pages` are not rejected by `Config` (silently ignored by `build_plan`): a Config-level check is still open.
- typer 0.27 bundles click: do not import `click`. `typer>=0.12` added to pyproject.

### Task 2: YAML loading
- `agenda.configfile`: `load_yaml(path) -> dict` (flat Config kwargs; `booklet: {size,unit,folded}` -> `booklet_*` via `flatten`; empty file = `{}`), `merge(yaml, overrides)` (CLI wins per key), `ConfigFileError(ValueError)`.
- `run --config PATH`: `Config(**merge(load_yaml, build_overrides))` is the single validation; unknown keys fail in Config (`extra=forbid`). All errors exit 2 with `agenda-gen: ...`.
- Overrides replace whole values: `--pages`/`--category` replace the YAML `pages`; `--preset` is ignored if YAML sets `pages` (explicit pages win). Output path: flag, else YAML `output`, else `DEFAULT_OUTPUT`.
- `Config.pages` still accepts unknown ids (left open; not Config-trivial because catalog imports config).

### Task 3: `--list`
- `catalog.catalog_rows()` (dicts: id, name, category, value, presets; sorted category, value desc, id) and pure `format_catalog(rows) -> str` (aligned table, `-` = unscored/none). No new module.
- `--list` is an eager flag on `run` (like `--version`): prints and exits 0 before any other arg is validated. Tests: `tests/test_catalog_list.py`, `test_cli.py` (`--list` example).
