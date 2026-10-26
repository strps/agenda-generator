# ADR 0001: Config fields are the single source of help text and CLI flags

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-structure-cleanup (structure-cleanup/04, structure-cleanup/05)

## Context
Per-field help (tooltips, details) and ~70 CLI options were hand-written in separate places
(agenda/gui/help_text.py, agenda/cli.py) and drifted from Config.

## Decision
Every Config field carries description/detail/cli metadata; agenda/fields.py exposes it
(short_help, detail_help, cli_meta, field_names). help_text.py builds PARAM_SHORT/PARAM_DETAILS
from it and stays Qt-free plain text (may import agenda.fields, never PySide6). agenda/cli.py
generates field options from cli_meta; only non-field options (--version, --list, --config,
--category, --page-range, --blank-pages, --dry-run) and pages/qr_urls (cli skip) are hand-written.
The flag surface is pinned by tests/test_cli_flags.py and old help text by tests/data/param_help.json.

## Consequences
A new field needs: metadata on Config, its templates.SECTIONS entry, a settings_model kind only if
special, and docs. Changing a flag means updating the pin deliberately. Any change to how
user-facing strings are produced (e.g. translation) must go through agenda/fields.py.
