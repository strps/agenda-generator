# CLAUDE.md

- Ruff is clean (check + format); keep it so. Run tests with `.venv/bin/python -m pytest` and `QT_QPA_PLATFORM=offscreen`.
- Phased planning lives in docs/agent/ (PLAN.md, STATE.md, BACKLOG.md); long-lived decisions in docs/adr/README.md.
- GUI/CLI user-visible text goes through `agenda.uitext.tr()`, never `agenda/i18n.py` (PDF only).
- GUI tests that build MainWindow must `wait_idle()` and `close()` it, or a background pdfium render segfaults a later test.
