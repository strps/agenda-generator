# Phase 7b handoff

Short running notes between agents. Trim stale entries.

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- GUI code only under `agenda/gui/`; core and CLI never import PySide6 (`gui` is an optional extra).
- Rules live in `Config` only; widgets map to Config fields and never re-check them.
- Pure logic (layout math, state) in Qt-free modules with unit tests; widget tests use a plain `QApplication` fixture with `QT_QPA_PLATFORM=offscreen`, skipped if PySide6 is missing.

## Log
### Task 1: main window
- `agenda.gui.layout` (Qt-free): `REGIONS`, `WindowLayout` (title, size, `splitter_sizes()`).
- `agenda.gui.app`: `MainWindow` with `regions: dict[name, QWidget]` (toolbar, settings, preview, section_bar, legend, summary, export); buttons `open_button`, `save_button`, `export_button` (unwired). `main(argv)` is the `agenda-gui` entry point; also `python -m agenda.gui`.
- Settings/preview/bar/legend/summary are `QFrame` placeholders with a label: replace them (keep the object names) in later tasks. Only `gui` and `gui.layout` are in the smoke MODULES (`gui.app` needs PySide6).
- Tests: `tests/test_gui_shell.py`.
### Task 2: settings panel
- `gui.settings_model` (Qt-free, in smoke MODULES): `field_specs()` (FieldSpec kind/choices/default/min/max from `Config.model_fields`), `default_values`, `build_config(values) -> (Config|None, msg)`, `save_yaml(cfg, path)` (flat keys, None omitted), `load_values(path)` (defaults + `load_yaml`; unknown keys kept so Config rejects them).
- `gui.settings_panel.SettingsPanel` (`QFrame`, object name `settings`): `editors[name]`, `values()`, `set_values()`, `config()`, `load_file`/`save_file`, signal `changed` (fires per edit and after set_values; task 5 debounces it). Pages = checklist by category; none checked = `pages: None`.
- `MainWindow.settings`, `load_config(path)`/`save_config(path)` return "" or an error; buttons open QFileDialog.
- Tests: `tests/test_gui_settings.py`.
### Task 3: render_pages
- `agenda.exporter.render_pages(cfg, plan, indices) -> bytes`: 0-based plan indices, plan order, dupes ignored; empty -> ValueError, out of range -> IndexError.
- Shares `_render_plan` with `export_agenda` (all pages = same output). `add_page(pdf, cfg, page_number=None)` takes the real page number.
- A spread (2-page instance) is drawn whole and the unrequested page dropped with pypdf, so one index = one PDF page.
- Tests: `tests/test_render_pages.py` (compares text + `drawn_points`; raw streams differ by font subset).
### Task 4: preview
- `gui.preview_model` (Qt-free, in smoke MODULES): `display_rows(mode, index, total, booklet_of, folded)` -> rows of 0-based plan indices (single / spread (even,odd) / sheet rows [front, back], saddle-stitch order); `render_indices`, `pdf_position`, `step` (by page/spread/sheet), `zoom_scale` (fit or % ; 100% = 96 dpi), `label`, `effective_mode` (sheet falls back to spread if not folded).
- `gui.preview.PreviewWidget` (object name `preview`): `set_plan(cfg, plan)`, `set_error(text)`, `set_mode`, `set_zoom`, `goto`, `move`, `refresh`, signal `page_changed(index)`; `rasterise(pdf_bytes, scale)` via pypdfium2 (BGR888 QImage). Page labels live in `.grid`.
- `MainWindow.preview` + `update_preview()` run on `settings.changed`, synchronously (build_plan + render_pages in the GUI thread): task 5 moves this to a worker + cache + debounce.
- Sheet mode is computed from `booklet_index` (no imposition module yet); pages outside booklets show as a spread. Debug-grid checkbox from gui.md not added (it is a Config field in settings).
- Tests: `tests/test_gui_preview.py`.
