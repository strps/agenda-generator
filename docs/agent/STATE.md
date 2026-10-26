# STATE: agenda-generator        (rewritten each phase, max 80 lines)
Last phase: 09
## Decisions in force
- ExpandingToolTip filters only the top widget (+ viewport); no descendant filters, since Leave fires between children (phase 08)
- help_text.py is Qt-free and plain text (no HTML); it imports only bar_model.SECTION_LABELS, never Config/pydantic (phase 01, 07)
- Tests run via `.venv/bin/python -m pytest` (bare `pytest`/`python` not on PATH); set QT_QPA_PLATFORM=offscreen (phase 01)
- Main toolbar tooltips set once in MainWindow.__init__; `_sync_export_button` sets export tooltip to TOOLTIPS["export_pdf"], plus "\n\n"+EXPORT_DISABLED_REASON when invalid (phase 02)
- Preview nav tooltips set in PreviewWidget.__init__ from TOOLTIPS; mode uses TOOLTIPS[f"mode_{m}"] (KeyError if missing) (phase 03)
- Legend: persistent `Legend.title` QLabel (objectName legend_title) is re-added after each set_entries rebuild, never deleted; button and swatch share tooltip `section_tooltip(key)\nClick to go to the first <Label> page.` (phase 04)
- Padding swatch is a QLabel with a 12x12 QPixmap (gray + BDiagPattern in window color); other swatches use stylesheet background; `recolor()` handles both and runs on PaletteChange (phase 05)
- SectionBar hover: `hover_at(x, global_pos=None)` tracks section key (padding -> B.PADDING); single-shot `expand_timer` (made by hover_tooltip.make_expand_timer) starts only when the section changes; `_expand` appends `help_text.section_tooltip`; `reset_hover()` on leave, press/drag, set_plan, empty space (phase 06)
- Param texts: PARAM_SHORT/PARAM_DETAILS keyed by Config field name, cover every field, details name cross-field rules and list Literal choices; test derives names from Config.model_fields (phase 07)
- SettingsPanel: `tooltips[name]` ExpandingToolTip on every editor (incl. `pages` group box); non-pages rows use explicit QLabel `label_<name>` with `label_tooltips[name]`; attached in __init__ after _make (phase 09)
- SettingsPanel: `tooltips[name]` ExpandingToolTip per editor (pages: on the group box), `label_tooltips[name]` per QLabel `label_<name>` row label (not pages); attached in __init__ after _make (phase 09)

## Interfaces
- agenda/gui/help_text.py: `TOOLTIPS` (ids open_config, save_config, export_pdf, prev, next, mode_single, mode_spread, mode_sheet, zoom), `EXPORT_DISABLED_REASON`, `SECTION_DESCRIPTIONS`, `section_tooltip(key)`, `PARAM_SHORT`, `PARAM_DETAILS`, `param_tooltip(name, expanded=False)` (short, or short+"\n"+detail; unknown name returns name)
- agenda/gui/hover_tooltip.py: `HOVER_EXPAND_MS=1500` (only definition; re-exported by section_bar), `make_expand_timer(parent, slot)`, `ExpandingToolTip(widget, short, detail)` (event filter on widget + scroll-area viewport; members expand_timer, expanded, hover(global_pos=None), current_text(), reset(), set_texts(short, detail)); Enter starts timer, ToolTip shows current text (consumed; fallback starts timer), Leave/Hide reset; tests/test_gui_hover_tooltip.py
- section_bar.py: `HOVER_EXPAND_MS` (imported), `SectionBar.expand_timer`, `hover_at`, `current_tooltip`, `reset_hover`; tests in tests/test_gui_bar_hover.py
- tests/test_gui_tooltips.py: has module-scoped `qapp` fixture; main toolbar + preview nav tests; toolbar-region check covers win.preview and the toolbar parent of open_button (legend/settings excluded)
- tests/test_gui_settings_tooltips.py: settings editor/label tooltip tests
- tests/test_gui_param_help.py: Qt-free tests for param texts (derive names from Config.model_fields)

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen
