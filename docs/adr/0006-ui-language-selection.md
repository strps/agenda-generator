# ADR 0006: The UI language is chosen per user, at startup, separately from the agenda language

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-ui-i18n (ui-i18n/01, ui-i18n/06)

## Context
The GUI and CLI became translatable (ADR 0005). The printed agenda already has its own
`Config.language`, which belongs to the agenda file, while the interface language belongs to the
person using the app. Live retranslation of open windows would touch every widget.

## Decision
The UI language is resolved once at startup: saved GUI preference (QSettings key `ui_language`:
system|en|es) > `AGENDA_UI_LANG` (valid values only) > system locale (LC_ALL, LC_MESSAGES, LANG in
POSIX order; es* → es) > en. The GUI resolves it via uitext.startup_language in main() before any
widget; the CLI from the environment. A change in Preferences applies on restart (the dialog says so).
`ui_language` is never written to YAML and is independent of `Config.language`.

## Consequences
Widgets can read text once at construction; no retranslation code. Adding live switching later needs
a new ADR. A config.yaml never carries UI language, so shared agenda files don't impose one. Tests
pin English via AGENDA_UI_LANG=en in tests/conftest.py.
