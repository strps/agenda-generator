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
