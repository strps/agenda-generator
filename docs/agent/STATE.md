# STATE: agenda-generator        (rewritten each phase, max 80 lines)
Last phase: 02
## Decisions in force
- help_text.py is Qt-free and plain text (no HTML); it imports only bar_model.SECTION_LABELS (phase 01)
- Tests run via `.venv/bin/python -m pytest` (bare `pytest`/`python` not on PATH); set QT_QPA_PLATFORM=offscreen (phase 01)
- Main toolbar tooltips set once in MainWindow.__init__; `_sync_export_button` sets export tooltip to TOOLTIPS["export_pdf"], plus "\n\n"+EXPORT_DISABLED_REASON when invalid (phase 02)

## Interfaces
- agenda/gui/help_text.py: `TOOLTIPS` (ids open_config, save_config, export_pdf, prev, next, mode_single, mode_spread, mode_sheet, zoom), `EXPORT_DISABLED_REASON`, `SECTION_DESCRIPTIONS` (keys = SECTION_LABELS), `section_tooltip(key) -> "<Label>: <desc>"`, unknown key returns key
- tests/test_gui_tooltips.py: has module-scoped `qapp` fixture; phase 03 appends preview tests

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen
