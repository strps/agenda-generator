# STATE: agenda-generator        (working memory of the active plan, rewritten each phase, max 40 lines)
Plan: 2026-10-26-ui-i18n
Last phase: 06
ADRs: docs/adr/README.md (long-lived decisions; read the index, open an ADR only when your phase touches it)

## Decisions (this plan)
- Catalog is agenda/uitext (Qt-free), separate from agenda/i18n.py: PDF strings must stay byte-identical (ui-i18n/01)
- Tables are `MESSAGES` dicts in uitext/en.py (source of truth, fallback) and uitext/es.py (ui-i18n/01)
- system_language: AGENDA_UI_LANG (valid only) else first non-empty of LC_ALL, LC_MESSAGES, LANG (POSIX precedence) (ui-i18n/01)
- Language is lazily initialized from os.environ; conftest sets AGENDA_UI_LANG=en and an autouse fixture resets to en (ui-i18n/01)
- ADR 0005 records the plan's catalog decisions (ui-i18n/01)
- Spanish Config/section/group text is Spanish-only in uitext/es_fields.py (merged into the es table in __init__, not in es.MESSAGES, so es==en key test still holds); English stays on Config/templates.py (ui-i18n/02)
- GUI text tables are lazy: uitext.Table(prefix, keys) Mapping (TOOLTIPS, EXPORT_HELP, SECTION_DESCRIPTIONS, SECTION_LABELS, PAD_SHORT, FILLER_TEXT); EXPORT_FIELDS/EXPORT_DISABLED_REASON/NO_PLAN_TEXT via module __getattr__; WindowLayout.title is a default_factory (ui-i18n/03)
- GUI tests that build MainWindow after set_language("es") must wait_idle() and close() it, else a pdfium worker segfaults a later test (ui-i18n/05)
- Combo items: translated text + item data, read via currentData(); export dialog groupboxes keep English objectNames via _GROUP_KEYS (ui-i18n/04)
- Dates in bar tooltips use catalog month/weekday names (date.*), not strftime/calendar, so es works without OS locales (ui-i18n/03)
- uitext.lookup(key) returns raw text (no format, no English fallback) because texts contain literal {n} (ui-i18n/02)
- GUI language: QSettings key ui_language (system|en|es); main() calls uitext.startup_language(pref, QLocale name) = pref > AGENDA_UI_LANG > locale > en; applies on restart, dialog shows prefs.restart_note when changed; not added to configfile.LEGACY_GUI_KEYS (never in YAML) (ui-i18n/06)

## Contracts (between this plan's phases)
- Catalog API: agenda/uitext/__init__.py::tr, startup_language, set_language, get_language, keys, resolve_language, system_language, LANGUAGES
- Localized accessors: agenda/fields.py::short_help/detail_help/field_label, agenda/templates.py::section_label/group_label (app, export dialog and settings_panel use them)
- Lint: tests/test_ui_strings_lint.py::violations(source) is the AST checker; every agenda/gui/*.py is scanned (no allowlist left)
- Catalog keys by area: app.*, prefs.*, export.title/all/browse/layout.*, tooltip.*, export.help.*, section_desc.*, bar.section.*, export.group.*, summary.*, pad.*, page.*, header.*, date.*, preview.*; uitext.Table in agenda/uitext/__init__.py
- help_text.PARAM_SHORT/PARAM_DETAILS are lazy Mappings (_FieldTexts)
- Add keys to both agenda/uitext/en.py and es.py MESSAGES; tests/test_uitext.py checks keys and placeholders generically

## Open issues
- template_model.PAD_FIELDS second tuple element (English use text) is now unused by pad_text
- settings_model messages are pydantic text (out of scope), nothing converted there

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- GUI/CLI user-visible text goes through agenda.uitext.tr(), never agenda/i18n.py (PDF only)
