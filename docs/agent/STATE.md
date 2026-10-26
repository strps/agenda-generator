# STATE: agenda-generator        (working memory of the active plan, rewritten each phase, max 40 lines)
Plan: 2026-10-26-ui-i18n
Last phase: 02
ADRs: docs/adr/README.md (long-lived decisions; read the index, open an ADR only when your phase touches it)

## Decisions (this plan)
- Catalog is agenda/uitext (Qt-free), separate from agenda/i18n.py: PDF strings must stay byte-identical (ui-i18n/01)
- Tables are `MESSAGES` dicts in uitext/en.py (source of truth, fallback) and uitext/es.py (ui-i18n/01)
- system_language: AGENDA_UI_LANG (valid only) else first non-empty of LC_ALL, LC_MESSAGES, LANG (POSIX precedence) (ui-i18n/01)
- Language is lazily initialized from os.environ; conftest sets AGENDA_UI_LANG=en and an autouse fixture resets to en (ui-i18n/01)
- ADR 0005 records the plan's catalog decisions (ui-i18n/01)
- Spanish Config/section/group text is Spanish-only in uitext/es_fields.py (merged into the es table in __init__, not in es.MESSAGES, so es==en key test still holds); English stays on Config/templates.py (ui-i18n/02)
- uitext.lookup(key) returns raw text (no format, no English fallback) because texts contain literal {n} (ui-i18n/02)

## Contracts (between this plan's phases)
- Catalog API: agenda/uitext/__init__.py::tr, set_language, get_language, keys, resolve_language, system_language, LANGUAGES
- Localized accessors: agenda/fields.py::short_help/detail_help/field_label, agenda/templates.py::section_label/group_label (callers still use SectionSpec.label/name.replace until phases 03-05)
- help_text.PARAM_SHORT/PARAM_DETAILS are lazy Mappings (_FieldTexts)
- Add keys to both agenda/uitext/en.py and es.py MESSAGES; tests/test_uitext.py checks keys and placeholders generically

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- GUI/CLI user-visible text goes through agenda.uitext.tr(), never agenda/i18n.py (PDF only)
