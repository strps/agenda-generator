# STATE: agenda-generator        (rewritten each phase, max 80 lines)
Last phase: 01
## Decisions in force
- help_text.py is Qt-free and plain text (no HTML); it imports only bar_model.SECTION_LABELS (phase 01)
- Tests run via `python -m pytest` (bare `pytest` not on PATH) (phase 01)

## Interfaces
- agenda/gui/help_text.py: `TOOLTIPS` (ids open_config, save_config, export_pdf, prev, next, mode_single, mode_spread, mode_sheet, zoom), `EXPORT_DISABLED_REASON`, `SECTION_DESCRIPTIONS` (keys = SECTION_LABELS), `section_tooltip(key) -> "<Label>: <desc>"`, unknown key returns key

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- none
