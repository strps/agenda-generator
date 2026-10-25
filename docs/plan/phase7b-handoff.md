# Phase 7b handoff

## Conventions

- Env: `.venv/bin/pytest`, `.venv/bin/ruff check .`, `.venv/bin/ruff format --check agenda tests`.
- GUI code only under `agenda/gui/`; core and CLI never import PySide6 (`gui` is an optional extra).
- Rules live in `Config` only; widgets map to Config fields and never re-check them.
- Pure logic (layout math, state) in Qt-free modules with unit tests; widget tests use a plain `QApplication` fixture with `QT_QPA_PLATFORM=offscreen`, skipped if PySide6 is missing.

## Log
- T1 main window: `gui.layout` (REGIONS, WindowLayout); `MainWindow.regions`, buttons open/save/export; legend/summary are placeholder QFrames (keep object names). Tests `test_gui_shell.py`.
- T2 settings: `gui.settings_model` (field_specs, build_config, save_yaml, load_values); `SettingsPanel` (`editors`, `values`, `config`, signal `changed`); `MainWindow.load_config/save_config`.
- T3 `exporter.render_pages(cfg, plan, indices)`: 0-based, plan order, one index = one PDF page.
- T4 preview: `gui.preview_model` (display_rows, step, sheet_rows, sheet_number, label, zoom_scale); `PreviewWidget` (`set_plan`, `goto`, `move`, `refresh`, signal `page_changed(index)`).
- T5 `gui.render_cache` (config_hash, LruCache, Debounce, LatestGate), `gui.workers` (RenderJob); refresh is async (`wait_idle` in tests); settings.changed -> 300 ms -> `update_preview()`; `flush_preview()` skips wait.
- T6 `gui.bar_model` (geometry, segments, ticks, marker_x, GAP_PX=2, PADDING key); `SectionBar` (`set_plan`, `set_position`, `geometry_for`).
- T7 `gui.section_colors` (PALETTE, `section_color(key, dark)`, `is_dark`); `SectionBar.color_for`. Legend (T9) should reuse `section_color`.
### Task 8: bar interaction
- `bar_model`: `BarGeometry.page_at(x)` (clamps; gap -> nearer page; None if empty), `tooltip_text(plan, i)` ("Page 143 · Weekly · Week 12 (Mar 16–22) · Booklet 8, sheet 2"), `key_target(key, index, plan)` (left/right = spread, pageup/pagedown = booklet start, home/end), `first_page_of(plan, section)`, `SECTION_LABELS` (T9 legend can reuse).
- `SectionBar`: signal `page_requested(int)` (click, drag, keys; focusable), `tooltip_for(x)`, `first_page_of(section)` = legend-click hook (emits). `MainWindow` connects it to `preview.goto`.
- Tests: `tests/test_gui_bar.py` (QTest click/drag/keys).
### Task 9: legend + summary
- `gui.legend_model` (`legend_entries(plan)` -> LegendEntry(key,label,count), `summary_text`/`summary_tooltip` from `summarize`, `NO_PLAN_TEXT`); `Legend` widget (`entries`, `buttons`, `set_entries`, `recolor`, signal `section_clicked(key)` -> `section_bar.first_page_of`).
- `MainWindow.legend`, `.summary_label` (real widgets replacing placeholders); both updated in `update_preview`; config error -> empty legend + NO_PLAN_TEXT.
### Task 10: export
- Core: `export_agenda(cfg, path, progress=None)`; `progress(done, total)` after each page, output unchanged.
- `gui.export_model` (`default_path`, `ensure_pdf`, `progress_fraction/percent`), `gui.export_job` (`ExportJob`, `ExportSignals`).
- `MainWindow.start_export(path)` / `export_dialog()` / `wait_export()`, `export_progress`, `export_status`, `export_result`; button disabled while running or config invalid.
- `tests/test_gui_export.py` compares GUI vs CLI (`--config`) by text + drawn points.
