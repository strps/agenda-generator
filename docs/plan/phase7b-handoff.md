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
