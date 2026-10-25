# STATE: agenda-generator        (rewritten each phase, max 80 lines)
Last phase: 06
## Decisions in force
- help_text.py is Qt-free and plain text (no HTML); it imports only bar_model.SECTION_LABELS (phase 01)
- Tests run via `.venv/bin/python -m pytest` (bare `pytest`/`python` not on PATH); set QT_QPA_PLATFORM=offscreen (phase 01)
- Main toolbar tooltips set once in MainWindow.__init__; `_sync_export_button` sets export tooltip to TOOLTIPS["export_pdf"], plus "\n\n"+EXPORT_DISABLED_REASON when invalid (phase 02)
- Preview nav tooltips set in PreviewWidget.__init__ from TOOLTIPS; mode uses TOOLTIPS[f"mode_{m}"] (KeyError if missing) (phase 03)
- Legend: persistent `Legend.title` QLabel (objectName legend_title) is re-added after each set_entries rebuild, never deleted; button and swatch share tooltip `section_tooltip(key)\nClick to go to the first <Label> page.` (phase 04)
- Padding swatch is a QLabel with a 12x12 QPixmap (gray + BDiagPattern in window color); other swatches use stylesheet background; `recolor()` handles both and runs on PaletteChange (phase 05)
- SectionBar hover: `hover_at(x, global_pos=None)` tracks section key (padding -> B.PADDING); single-shot `expand_timer` (HOVER_EXPAND_MS=1500) starts only when the section changes; `_expand` appends `help_text.section_tooltip`; `reset_hover()` on leave, press/drag, set_plan, empty space (phase 06)

## Interfaces
- agenda/gui/help_text.py: `TOOLTIPS` (ids open_config, save_config, export_pdf, prev, next, mode_single, mode_spread, mode_sheet, zoom), `EXPORT_DISABLED_REASON`, `SECTION_DESCRIPTIONS` (keys = SECTION_LABELS), `section_tooltip(key) -> "<Label>: <desc>"`, unknown key returns key
- section_bar.py: `HOVER_EXPAND_MS`, `SectionBar.expand_timer`, `hover_at`, `current_tooltip`, `reset_hover`; tests in tests/test_gui_bar_hover.py
- tests/test_gui_tooltips.py: has module-scoped `qapp` fixture; has main toolbar + preview nav tests; toolbar-region check covers win.preview and the toolbar parent of open_button (legend/settings excluded)

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen
