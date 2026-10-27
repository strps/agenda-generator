# ADR 0007: Rules for user-visible UI text

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-ui-i18n (ui-i18n/03, ui-i18n/04, ui-i18n/05)

## Context
Once every GUI string was moved into the catalog, new hard-coded strings, missing translations and
locale-dependent formatting would silently bring English back or break Spanish.

## Decision
- Every agenda/gui/*.py file is scanned by an AST lint test (tests/test_ui_strings_lint.py) with no
  allowlist; user-visible literals must go through the catalog.
- Every key is added to both agenda/uitext/en.py and es.py; tests check matching keys and placeholders.
- Dates shown in the UI use the catalog's month/weekday names, not strftime/calendar, so Spanish
  works without OS locales installed.
- Combo boxes show translated text and store the raw value as item data (read via currentData());
  objectNames stay English so code and tests do not depend on the language.

## Consequences
A new widget string fails the lint until it gets a key in both tables. Code must never compare
against displayed text. Adding a language means one more table that passes the same parity tests.
