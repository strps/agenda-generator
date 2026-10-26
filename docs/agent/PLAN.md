# PLAN: App UI internationalization (GUI and CLI in English and Spanish)

Plan: 2026-10-26-ui-i18n
Goal: Every user-visible GUI and CLI string goes through a Qt-free UI catalog with English (default/fallback) and Spanish, the language picked from a GUI preference or the environment, without changing the printed PDF.
Backlog: App internationalization (i18n): translatable GUI/CLI strings and localized output
Out of scope: the printed-PDF strings (agenda/i18n.py STRINGS, Config.language, PDF output and tests/data/default_style_fingerprint.json stay byte-identical); Config/pydantic validation messages and agenda/configfile.py errors (stay English, shown as-is); catalog page titles and `--list` output; agenda/assembler.py summarize() text; click/typer built-in help boilerplate ("Options", "Show this message and exit."); live retranslation of open windows (a language change applies on restart); new languages beyond en/es; Babel/gettext/Qt Linguist
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
Constraints: no new dependencies; keep existing GUI models and public API stable; every existing config.yaml must keep loading to the same Config; Qt-free logic lives in Qt-free modules (e.g. agenda/gui/export_model.py) and is tested without PySide6; every new option gets a tooltip (help_text) and a CLI equivalent where one is missing; user-visible GUI/CLI text goes through the UI catalog (agenda/uitext), never through agenda/i18n.py
Commit per phase: yes

<!--
Header lines. Plan, Goal, Backlog and Out of scope belong to ONE plan: the
phase-planner sets them, /close-plan archives them and resets them to "none"/"-".
Stack, Verify command, Constraints and Commit per phase belong to the project
and survive every close-out.

Plan id: YYYY-MM-DD-<slug>. Phase commits are "<slug>/NN: <title>", review
fixes "<slug>/NN: fix review", decisions in STATE.md are tagged (<slug>/NN).

Status values: pending | in-progress | done | blocked
The Review line is filled in by run-plan: PASS, or FAIL -> fixed -> PASS.
Only the run-plan orchestrator changes status tags. You can edit them by hand
(e.g. set a blocked phase back to pending after answering its question).
-->

<!--
Planner findings (2026-10-26):
- agenda/i18n.py: PDF-only STRINGS es/en, DEFAULT_LANGUAGE "es", t()/Strings. Must not change.
- GUI string sinks (setText/setToolTip/QLabel/QPushButton/QAction/addMenu/setWindowTitle/
  QMessageBox/showMessage...): ~93 calls in app.py(26), settings_panel.py(15), preview.py(15),
  export_dialog.py(14), collapsible.py(9), style_editors.py(6), prefs_dialog.py(3), legend.py(3),
  hover_tooltip.py(2); section_bar.py too.
- Qt-free text sources: gui/help_text.py (TOOLTIPS, EXPORT_HELP, EXPORT_DISABLED_REASON,
  SECTION_DESCRIPTIONS, PARAM_SHORT/PARAM_DETAILS built at import from agenda.fields),
  gui/bar_model.py SECTION_LABELS, gui/template_model.py notices, gui/export_model.py group titles
  ("Page numbers", "Layout", "Booklets", "Output") and "page range: ..." errors,
  gui/legend_model.py, gui/preview_model.label(), gui/layout.py WindowLayout.title,
  templates.py SectionSpec.label / GroupSpec.label, field labels = name.replace("_", " ")
  (settings_panel.py:111, export_dialog.py:217).
- Prefs: QSettings(PREFS_ORG="agenda-gen", PREFS_APP="agenda-gui") in gui/app.py; key
  "appearance"; GuiSettingsDialog in gui/prefs_dialog.py holds values, caller persists.
- CLI: typer; help strings built at import of agenda/cli.py (app help, hand options, field
  options via fields.short_help); messages: _fail "agenda-gen: ...", "warning: unknown theme",
  "page range: ...", "wrote {out}".
- Pins in English: tests/data/param_help.json, tests/test_cli_flags.py, tests/test_gui_help_text.py.
-->

<!--
Decisions (2026-10-26, planner):
- Catalog: new Qt-free package agenda/uitext/ (separate from agenda/i18n.py). Dotted message keys
  (same convention as agenda/i18n.py), str.format fields. agenda/uitext/en.py is the source of truth
  for GUI/CLI-own strings; agenda/uitext/es.py holds the Spanish table.
- Config field help (ADR 0001) and section/group labels (ADR 0004) keep their English source where
  it is (Config metadata, templates.py). Spanish lives in the catalog under
  `field.<name>.short`, `field.<name>.detail`, `field.<name>.label`, `section.<key>`, `group.<key>`;
  agenda/fields.py and templates.py accessors return the translation for the current UI language
  and fall back to the English source. English field label = name.replace("_", " ").
- UI languages: ("en", "es"), default/fallback "en". Resolution: explicit preference
  ("en"/"es") wins; "system" or none -> system locale (es* -> es, else en).
  Env: AGENDA_UI_LANG (en|es) first, then LC_ALL, LC_MESSAGES, LANG (read from os.environ; no
  `locale` module). GUI preference QSettings key "ui_language", values system|en|es, default system;
  GUI system locale comes from QLocale.system().name() passed into the Qt-free resolver.
- Language is set once per process (uitext.set_language) before any window is built; changing it
  in Preferences is persisted and applies on restart (the dialog says so). Module-level text tables
  become lazy (Mapping subclasses / PEP 562 module __getattr__) so they read the current language at
  lookup time and keep their names and dict API.
- tests/conftest.py forces AGENDA_UI_LANG=en (and uitext language en) so the English pins hold on
  any host locale.
-->

## Phase 01 — Qt-free UI catalog core   [status: pending]
Deliverable: package agenda/uitext/ with `LANGUAGES = ("en", "es")`, `DEFAULT = "en"`, `ENV_VAR = "AGENDA_UI_LANG"`, `system_language(environ) -> str`, `resolve_language(pref: str | None, system_locale: str | None) -> str`, `set_language(lang)`, `get_language()` (lazily initialized from the environment on first use), `tr(key, **fmt)` (current language, falls back to English, raises KeyError naming the key when missing in English too), `keys()`; en.py/es.py tables seeded with a few common keys (e.g. `common.ok`, `common.cancel`, `prefs.restart_note`); tests/conftest.py forces English; ADR 0005 recording the decisions above, indexed in docs/adr/README.md.
Files: agenda/uitext/__init__.py, agenda/uitext/en.py, agenda/uitext/es.py, tests/test_uitext.py, tests/conftest.py, docs/adr/0005-ui-catalog.md, docs/adr/README.md
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and `.venv/bin/python -m pytest tests/test_uitext.py` (no PySide6 import: `grep -rn PySide6 agenda/uitext` is empty) covers: es keys == en keys; same `{placeholder}` names per key in en and es; resolve_language("system", "es_PE.UTF-8") == "es", ("system", "fr_FR") == "en", ("en", "es_ES") == "en", (None, None) == "en"; system_language honors AGENDA_UI_LANG over LC_ALL over LC_MESSAGES over LANG; an invalid AGENDA_UI_LANG falls back to locale detection; tr of an unknown key raises KeyError; `git diff --stat main -- agenda/i18n.py tests/data/default_style_fingerprint.json` is empty.
Notes: Do not touch agenda/i18n.py (its DEFAULT_LANGUAGE "es" is the PDF default and is unrelated). Keep the completeness test generic over all keys so later phases get it for free. The conftest override must run before any agenda import (module top of tests/conftest.py: os.environ["AGENDA_UI_LANG"] = "en"); add an autouse fixture that restores uitext's language to "en" after each test so tests switching to es do not leak.
Review: -

## Phase 02 — Localized Config field help, field labels and section labels   [status: pending]
Deliverable: agenda/fields.py `short_help(name)`, `detail_help(name)` return the current UI language (Spanish from `field.<name>.short/.detail`, else the Config English source) and a new `field_label(name)`; templates.py gets `section_label(key)` and `group_label(key)` (English from SectionSpec/GroupSpec.label, Spanish from `section.<key>` / `group.<key>`); Spanish text for every Config field (short, detail, label) and every section and group in agenda/uitext/es_fields.py merged into the es table; gui/help_text.py PARAM_SHORT/PARAM_DETAILS become lazy mappings with the same keys.
Files: agenda/fields.py, agenda/templates.py, agenda/uitext/__init__.py, agenda/uitext/es_fields.py, agenda/gui/help_text.py, tests/test_fields.py, tests/test_uitext.py
Depends on: 01
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes (tests/data/param_help.json and tests/test_cli_flags.py unchanged and green), and new Qt-free tests assert: for every name in fields.field_names() and every templates.SECTIONS/GROUPS key, the es catalog has a non-empty short, detail (when the English detail is non-empty), label / section / group entry; with set_language("es"), short_help("year") != the English description and equals the es entry; with "en", outputs equal Config metadata exactly; `git diff main --stat -- tests/data/` is empty.
Notes: Do not edit the old ADR 0001 text (ADRs are append-only); ADR 0005 from phase 01 already says translation goes through agenda/fields.py. SectionSpec.label stays English (data model unchanged); callers switch to section_label() in later phases. es_fields.py is large but data-only.
Review: -

## Phase 03 — Qt-free GUI text tables through the catalog   [status: pending]
Deliverable: every string in gui/help_text.py (TOOLTIPS, EXPORT_HELP, SECTION_DESCRIPTIONS, EXPORT_DISABLED_REASON via module __getattr__, section_tooltip) and in the Qt-free models (gui/bar_model.py SECTION_LABELS, gui/template_model.py notices, gui/export_model.py group titles and page-range error texts, gui/legend_model.py, gui/preview_model.label(), gui/layout.py window title, gui/settings_model.py messages) comes from tr()/fields/templates accessors, with en and es entries; names and dict-like API unchanged.
Files: agenda/gui/help_text.py, agenda/gui/bar_model.py, agenda/gui/template_model.py, agenda/gui/export_model.py, agenda/gui/legend_model.py, agenda/gui/preview_model.py, agenda/gui/layout.py, agenda/gui/settings_model.py, agenda/uitext/en.py, agenda/uitext/es.py
Depends on: 02
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes with tests/test_gui_help_text.py, tests/test_gui_export_model.py, tests/test_gui_template_model.py unchanged, and a new Qt-free test (tests/test_uitext_models.py) asserts that with set_language("es") HT.TOOLTIPS["open_config"], HT.EXPORT_DISABLED_REASON, bar_model.SECTION_LABELS["monthly"] and export_model group titles equal their es catalog entries and differ from English, and with "en" they equal the previous English literals.
Notes: export_model's "page range: ..." error wraps a parse_page_range ValueError message; only the prefix/own sentence is translated (the inner message is core, out of scope). Dict keys, CLI flags and data values never change; only display text. The completeness test from phase 01 covers the new keys automatically.
Review: -

## Phase 04 — Catalog lint test; extract strings in app, prefs and export dialog   [status: pending]
Deliverable: tests/test_ui_strings_lint.py (Qt-free, AST-based) that scans agenda/gui/*.py and fails on a string literal or f-string containing a letter passed to a Qt text sink (QLabel, QPushButton, QCheckBox, QRadioButton, QGroupBox, QAction, QMenu constructors; setText, setToolTip, setStatusTip, setWhatsThis, setWindowTitle, setPlaceholderText, setTitle, addMenu, addItem, addItems, showMessage, QMessageBox.* static calls, ExpandingToolTip args) unless wrapped in tr(); a temporary `PENDING` allowlist of files not converted yet; app.py, prefs_dialog.py and export_dialog.py converted (field labels via fields.field_label, section labels via templates.section_label, appearance/layout combo items show translated text with the value kept in item data).
Files: tests/test_ui_strings_lint.py, agenda/gui/app.py, agenda/gui/prefs_dialog.py, agenda/gui/export_dialog.py, agenda/uitext/en.py, agenda/uitext/es.py, tests/test_gui_prefs_dialog.py, tests/test_gui_export_dialog.py
Depends on: 03
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, tests/test_ui_strings_lint.py has app.py, prefs_dialog.py and export_dialog.py NOT in PENDING, and the lint test has a self-test proving it flags a sample `QLabel("Hello")` and `x.setToolTip(f"Go {n}")` and accepts `QLabel(tr("k"))`, `QLabel("")` and object names passed to setObjectName.
Notes: Existing GUI tests that look widgets up by text may need to switch to objectName or keep working because the default language is en; prefer not to change assertions. Combo boxes: `addItem(tr(...), userData=value)` and read `currentData()`; keep `GuiSettingsDialog.appearance()` returning the raw value. The lint test must not import PySide6 (parse source with ast only).
Review: -

## Phase 05 — Extract strings in the remaining GUI widgets   [status: pending]
Deliverable: settings_panel.py, preview.py, legend.py, collapsible.py, style_editors.py, hover_tooltip.py, section_bar.py (and any other agenda/gui file the lint flags) use the catalog; PENDING allowlist in tests/test_ui_strings_lint.py is empty and removed.
Files: agenda/gui/settings_panel.py, agenda/gui/preview.py, agenda/gui/legend.py, agenda/gui/collapsible.py, agenda/gui/style_editors.py, agenda/gui/hover_tooltip.py, agenda/gui/section_bar.py, agenda/uitext/en.py, agenda/uitext/es.py, tests/test_ui_strings_lint.py (mechanical extraction phase; may exceed 10 files if the lint finds more)
Depends on: 04
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, `grep -n PENDING tests/test_ui_strings_lint.py` is empty, and a gui-marked test builds MainWindow after set_language("es") and asserts the open/save/export buttons, the Settings menu title and one settings-section header show the es catalog texts.
Notes: Section headers use templates.section_label/group_label; field labels use fields.field_label. Theme/color/font editor buttons and placeholders included. Do not change objectNames.
Review: -

## Phase 06 — UI language preference in the GUI   [status: pending]
Deliverable: Preferences dialog gets a Language combo (System / English / Español; values system|en|es) with tooltip from the catalog; MainWindow persists it under QSettings key "ui_language"; gui/app.py main() reads the preference before building any widget, resolves it with uitext.resolve_language(pref, QLocale.system().name()) and calls set_language; changing it shows a catalog note that it applies after restart; the window language does not change live.
Files: agenda/gui/prefs_dialog.py, agenda/gui/app.py, agenda/gui/help_text.py, agenda/uitext/en.py, agenda/uitext/es.py, agenda/uitext/__init__.py, tests/test_gui_prefs_dialog.py, tests/test_gui_shell.py, tests/test_uitext.py
Depends on: 05
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests assert: GuiSettingsDialog(appearance, ui_language="es").ui_language() == "es" and an unknown saved value shows "system"; accepting the dialog with "es" on a MainWindow built with a temporary QSettings (IniFormat in tmp_path) stores ui_language == "es"; a Qt-free helper (e.g. uitext.startup_language(pref, system_locale, environ)) returns "es" for (None, "es_AR", {}) and "en" for ("en", "es_AR", {}); the "language" Config field (PDF) is untouched by the preference (Config().language unchanged after setting ui_language).
Notes: Precedence for the GUI: saved preference (en/es) > AGENDA_UI_LANG > QLocale system > en. The appearance tooltip and the new language tooltip both state the choice is saved between runs. Never write ui_language into a config YAML (add it to the GUI-only prefs list in agenda/configfile.py only if that list is used for key rejection; check configfile.py:21).
Review: -

## Phase 07 — CLI help and messages through the catalog; docs   [status: pending]
Deliverable: agenda/cli.py app help, hand-written option help (--version, --list, --config, --category, --page-range, --blank-pages, --dry-run) and its own messages ("agenda-gen: ..." prefix sentence, unknown-theme warning, page-range errors, "wrote {out}") come from tr(); field option help comes from the localized fields.short_help; language from AGENDA_UI_LANG / LC_ALL / LC_MESSAGES / LANG; README and docs describe the GUI Language preference and AGENDA_UI_LANG, and note the difference from the PDF `language` field.
Files: agenda/cli.py, agenda/uitext/en.py, agenda/uitext/es.py, tests/test_cli.py, tests/test_cli_i18n.py, README.md, docs/ (user guide page that documents Preferences/CLI, if any)
Depends on: 02
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes with tests/test_cli_flags.py unchanged, and tests/test_cli_i18n.py runs `subprocess.run([sys.executable, "-m", "agenda", "--help"], env={..., "AGENDA_UI_LANG": "es"})` and finds the es catalog text of the app help and of `--dry-run`, while the same with AGENDA_UI_LANG=en (and with LANG=es_ES.UTF-8 plus AGENDA_UI_LANG unset) shows English resp. Spanish; `grep -n "AGENDA_UI_LANG" README.md` matches; `git diff main --stat -- agenda/i18n.py tests/data/` is empty.
Notes: typer builds help at import, so language must be resolved by uitext's lazy init from the environment (no CLI flag needed). Use `python -m agenda` (agenda/__main__.py) or the console entry; strip LC_*/LANG from the copied env in the en case. Errors coming from Config/configfile stay English (out of scope); only the wrapping text is translated. The docs-style tests (tests/test_docs_*.py) must stay green.
Review: -

## Open questions
- Config validation messages and agenda/configfile.py errors (shown in the GUI error view and CLI) stay English in this plan; translate them in a follow-up plan?
- The assembler summary line (GUI summary bar, --dry-run output) stays English; translate it in a follow-up?
