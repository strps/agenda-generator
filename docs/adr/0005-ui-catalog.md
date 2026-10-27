# ADR 0005: GUI and CLI text goes through a Qt-free catalog, separate from the PDF strings

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-ui-i18n (ui-i18n/01)

## Context
GUI and CLI text was hard-coded English. The printed-PDF strings live in agenda/i18n.py with
their own default language ("es") and must stay byte-identical.

## Decision
- New Qt-free package agenda/uitext/: dotted keys, `str.format` fields, `tr(key, **fmt)`.
  en.py is the source of truth and the fallback; es.py is the Spanish table.
- Config field help (ADR 0001) and section/group labels (ADR 0004) keep their English source in
  Config metadata and templates.py. Spanish lives in the catalog (`field.<name>.short|detail|label`,
  `section.<key>`, `group.<key>`); agenda/fields.py and templates.py accessors return the current
  language and fall back to English.
- UI languages ("en", "es"), default/fallback "en". An explicit preference wins; "system"/none uses
  the system locale (es* -> es). Env: AGENDA_UI_LANG, then LC_ALL, LC_MESSAGES, LANG, read from
  os.environ. GUI preference: QSettings key "ui_language" (system|en|es).
- Language is set once per process (`set_language`) before any window is built; a change applies
  on restart. Module-level text tables become lazy so they read the language at lookup time.
- tests force AGENDA_UI_LANG=en so English pins hold on any host.

## Consequences
agenda/i18n.py is never used for GUI/CLI text. Config validation messages, configfile errors and
assembler summaries stay English. New languages need a table plus an entry in LANGUAGES.
