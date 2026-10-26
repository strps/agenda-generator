# ADR 0003: Qt tests carry the `gui` pytest marker

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-structure-cleanup (structure-cleanup/02)

## Context
The suite mixed Qt and Qt-free tests with three different skip patterns; the core could not run
quickly or without PySide6.

## Decision
The `gui` marker is registered in pyproject.toml (with --strict-markers). Whole-Qt files set
`pytestmark = pytest.mark.gui`; mixed files decorate individual tests. tests/conftest.py ignores
files containing that pytestmark when PySide6 is missing (no module-level importorskip, which would
skip noisily under -m 'not gui').

## Consequences
`pytest -m "not gui"` runs the Qt-free core; plain Verify runs everything. New Qt test files must use
the same pytestmark; Qt-free logic belongs in Qt-free modules tested without PySide6.
