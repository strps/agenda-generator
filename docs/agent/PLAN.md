# PLAN: Export dialog

Goal: The GUI "Export PDF" button opens an export dialog where the user configures how the PDF is exported (page numbering, booklet/imposition output, and other relevant export options) before it is written; the choices map onto Config/exporter options, are remembered, and match the CLI. Phases 08+: the GUI's own look (dark/light/system appearance) moves out of the configuration panel into a separate GUI Settings (Preferences) dialog stored in QSettings, and the configuration panel's "Colors & styling" section instead controls the generated PDF's style (theme palette, individual colors, primary and secondary fonts), saved in config.yaml, with CLI flags, used by the export and the previews.
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
Constraints: no new dependencies; keep existing GUI models and public API stable; every existing config.yaml must keep loading to the same Config; Qt-free logic lives in Qt-free modules (e.g. agenda/gui/export_model.py) and is tested without PySide6; every new option gets a tooltip (help_text) and a CLI equivalent where one is missing
Commit per phase: yes
Out of scope: restyling the PDF output (phases 01-07 only; phases 08+ add user-selectable output colors/fonts but no layout, size or spacing changes); changing page templates; new imposition algorithms (only expose existing ones). Planner: first inspect exporter.py, imposition.py, export_job.py, export_model.py and the Config booklet/numbering fields to decide which export options already exist and which are new (page numbers on/off/start/position/format, single pages vs spreads vs booklet signatures, page range, output path, open-after-export).

<!--
Phases are written by the phase-planner agent, one block per phase:

## Phase 01 — <short title>   [status: …]
Deliverable: <what exists when done>
Files: <paths likely created/changed>
Depends on: none
Done when: <objective check, e.g. `pytest tests/test_core.py` passes>
Notes: <decisions, pitfalls>
Review: -

Status values: pending | in-progress | done | blocked
The Review line is filled in by run-plan: PASS, or FAIL -> fixed -> PASS.
Only the run-plan orchestrator changes status tags. You can edit them by hand
(e.g. set a blocked phase back to pending after answering its question).
-->

<!--
Planner findings (inventory, 2026-10-25):
- Exists and works: imposition (saddle-stitch 2-up per booklet, agenda/imposition.py
  impose_booklets/impose_pages, sheet auto-chosen letter|a4 via choose_sheet), crop_marks + bleed,
  booklet_size/unit/folded/num_booklets/separate_covers/pad_with (plan structure), output,
  debug_grid. CLI flags exist for all of them.
- Exists in Config/CLI/help_text but NOT implemented anywhere: page_numbers (nothing draws numbers),
  creep_mm (nothing reads it). page_numbers is implemented in phase 01; creep_mm stays as is
  (see Open questions).
- New options decided here: page_number_start, page_number_first, page_number_position, page_number_placement,
  page_number_format (Config); spreads, sheet_size (Config); page range (export-time argument,
  NOT a Config field, never saved); open-after-export and last export directory (GUI-only QSettings).
- Export fields stay FLAT in YAML (no new templates.SECTIONS entry, no new YAML block).
-->

## Phase 01 — Page numbering in the PDF   [status: done]
Deliverable: `page_numbers=True` actually prints page numbers, configurable by five new Config fields, each with a CLI flag and help texts.
Files: agenda/config.py, agenda/numbering.py (new, Qt-free), agenda/exporter.py, agenda/cli.py, agenda/gui/help_text.py, tests/test_page_numbers.py (new), tests/test_cli.py
Depends on: none
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, and tests/test_page_numbers.py contains passing tests that (a) export a SMALL config (`{"year": 2026, "planners": ["weekly"], "daily_months": []}`) with page_numbers=True and find the expected label text via pypdf `extract_text()` on page 5 and not on pages before page_number_first; (b) with page_numbers=False no page's text contains the label; (c) `main([... "--page-numbers", "--page-number-start", "10", "--page-number-format", "{n} / {total}", ...])` writes a PDF whose numbered first page shows "10 / "; (d) unit tests of numbering.label_for/x_for cover outer/center/inner on left and right pages.
Notes:
- New Config fields (all in the "Content" block next to page_numbers): `page_number_start: int = Field(1, ge=0, le=9999)` (number printed on the first numbered page); `page_number_first: int = Field(1, ge=1)` (1-based plan page that gets the first number; earlier pages unnumbered, e.g. 3 skips cover + inside cover); `page_number_position: Literal["outer","center","inner"] = "outer"`; `page_number_placement: Literal["margin","footer"] = "margin"` (margin = bottom margin band below the safe area, default; footer = inside the page footer band, drawn on top of it at the bottom of the safe area); `page_number_format: str = "{n}"` (field_validator: must contain "{n}", may contain only the placeholders {n} and {total}, 1-24 chars; check with string.Formatter().parse). Defaults keep every existing config.yaml loading to the same Config (tests/test_sample_files.py must stay green; do not edit config.yaml in this phase).
- agenda/numbering.py (imports Config only under TYPE_CHECKING): `label_for(cfg, page_number, total_pages) -> str | None` (None when page_numbers off or page_number < page_number_first; n = page_number - page_number_first + page_number_start; total = last printed n, i.e. total_pages - page_number_first + page_number_start); `align_for(side, position) -> "L"|"C"|"R"` (outer = away from binding: right page -> R, left page -> L; inner the opposite).
- Drawing: in exporter._render_plan, right after each page's content is drawn (and also for blank page_class=None pages) draw the label per page_number_placement: margin = bottom margin band (between grid.safe.y2 and page_h, vertically centered); footer = bottom of the safe area, inside the footer band, on the side opposite the day-page quote/extra text where those exist across grid.safe.x..safe.x2 with the alignment, Inter "" 7pt, theme muted/gray text color (reuse an existing token from agenda/tokens.py, do not add colors). Pages are drawn after the instance's last page is added, so draw labels per page using that page's pdf page index (`pdf.page = k` then restore) or record and draw after the loop; total_pages = len(plan) (full plan, also in render_pages so previews match the export).
- CLI: `--page-number-start`, `--page-number-first`, `--page-number-position`, `--page-number-placement`, `--page-number-format`, passed through build_overrides like the other fields.
- help_text: PARAM_SHORT + PARAM_DETAILS for the 5 new fields (tests/test_gui_param_help.py derives names from Config.model_fields and will fail otherwise); details name the rule "only used when page_numbers is on" and list the position choices. Update PARAM_DETAILS["page_numbers"] to mention the five options. The settings panel auto-generates editors from field_specs, so the new fields appear in the Global form automatically (check tests/test_gui_settings_tooltips.py stays green).
- Do not touch creep_mm.
Review: PASS

## Phase 02 — Reader spreads layout and sheet size   [status: done]
Deliverable: new Config fields `spreads` (2-up reader spreads in reading order) and `sheet_size` (auto|letter|a4 for both spreads and booklet imposition); crop marks allowed with either layout; CLI flags and help texts.
Files: agenda/config.py, agenda/imposition.py, agenda/exporter.py, agenda/cli.py, agenda/gui/help_text.py, tests/test_imposition.py, tests/test_exporter.py, tests/test_config.py, tests/test_cli.py
Depends on: 01
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including new tests that: (a) `spread_sides(n)` returns `[(None,1),(2,3),...]` with the last page alone on the left when n is even (e.g. n=4 -> [(None,1),(2,3),(4,None)]); (b) exporting SMALL with spreads=True gives `ceil((n+1)/2)` landscape pages (width > height) where n = len(build_plan(cfg)); (c) sheet_size="a4" gives 297x210 mm sheets (±0.5 mm via mediabox/MM_PT) for both spreads and imposition, "letter" gives 279.4x215.9; (d) Config(imposition=True, spreads=True, booklet_folded=True) raises ValueError; Config(spreads=True, crop_marks=True) is valid; Config(crop_marks=True) alone still raises; (e) `--spreads` and `--sheet-size a4` work through `main([...])`.
Notes:
- Fields (Look & output block): `spreads: bool = False`, `sheet_size: Literal["auto","letter","a4"] = "auto"`. Rules in Config._check_booklet_rules: imposition and spreads are mutually exclusive ("choose either imposition or spreads"); crop_marks requires imposition or spreads (loosened, existing configs still load identically); sheet_size is ignored for plain pages (no error).
- imposition.py: add `spread_sides(n) -> list[tuple[int|None,int|None]]` (page 1 is a right page, see grid.side_for_page) and `impose_spreads(pdf: bytes, sheet_mm=None, bleed_mm=None) -> bytes` built on impose_pages; add an optional `sheet_mm` parameter to impose_booklets passed to impose_pages. Map "auto" -> None, otherwise SHEETS[name]. No other algorithm changes (out of scope).
- exporter.export_agenda: branch on cfg.imposition / cfg.spreads; keep the untouched-output path byte-identical when both are off (test_core_progress_callback_does_not_change_output must stay green).
- CLI: `--spreads/--no-spreads`, `--sheet-size`. help_text PARAM_SHORT/DETAILS for both; update crop_marks/bleed/imposition details to say "imposition or spreads".
Review: PASS

## Phase 03 — Export page range (core + CLI)   [status: done]
Deliverable: export_agenda can write only a page range (plain-pages layout), exposed as CLI `--page-range "1-4,9"`; parsing is Qt-free and reusable by the GUI.
Files: agenda/pagerange.py (new), agenda/exporter.py, agenda/cli.py, agenda/gui/help_text.py, tests/test_pagerange.py (new), tests/test_exporter.py, tests/test_cli.py
Depends on: 02
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests that: `parse_page_range("1-3, 5", 10) == [1,2,3,5]`; `parse_page_range("", 10)` and `parse_page_range("all", 10)` return None (= all pages); "0", "4-2", "11", "a" raise ValueError with a message naming the bad token; exporting SMALL with page range "2-3" yields a 2-page PDF whose page texts equal pages 2-3 of the full export; `main([... "--page-range", "2-3", "--imposition", "--folded"])` exits with code 2 and an error mentioning the page range; `main([... "--page-range", "2-3"])` exits 0.
Notes:
- agenda/pagerange.py: `parse_page_range(text: str | None, total: int) -> list[int] | None` (1-based, sorted, de-duplicated; whitespace tolerant; "all"/empty/None -> None); `format_page_range(pages) -> str` (compresses runs, used by the dialog's CLI preview).
- exporter.export_agenda gains keyword `pages: Sequence[int] | None = None` (1-based); when given, use render_pages(cfg, plan, [p-1 for p in pages]) bytes and write them; progress still called. Raise ValueError if pages is given together with cfg.imposition or cfg.spreads ("a page range can only be exported as single pages"). Page labels (phase 01) keep their full-agenda numbers.
- Page range is NOT a Config field and is never saved to YAML. CLI parses it after Config validation (needs len(build_plan(cfg)) for the bound) and maps ValueError to exit code 2 via _fail.
- help_text: add `EXPORT_HELP` dict (Qt-free, plain text) with key "page_range" short + detail text; later phases add more GUI-only keys to it.
Review: PASS

## Phase 04 — Qt-free export dialog model   [status: done]
Deliverable: agenda/gui/export_model.py grows the logic the dialog needs: which fields it edits, layout mapping, enable rules, validation, and the equivalent CLI command; all tested without PySide6.
Files: agenda/gui/export_model.py, agenda/gui/help_text.py, tests/test_gui_export_model.py (new)
Depends on: 03
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_gui_export_model.py` passes without importing PySide6 (test asserts "PySide6" not in sys.modules after importing export_model, run in a subprocess or checked at module import) and the full suite passes. Tests cover: every name in EXPORT_FIELDS is a Config field and has PARAM_SHORT/PARAM_DETAILS; layout_of/with_layout round-trip for "pages", "spreads", "booklets" (booklets sets imposition=True, booklet_folded=True, spreads=False); field_enabled rules listed in Notes; `validate(values, page_range)` returns "" for a valid SMALL config and the Config error text otherwise; `cli_args(values, page_range, defaults)` run through `agenda.cli.main(args + ["--output", tmp])` produces the same page count as `export_agenda` with the same values.
Notes:
- EXPORT_FIELDS (ordered, grouped as a tuple of (group_title, fields)): "Page numbers": page_numbers, page_number_start, page_number_first, page_number_position, page_number_placement, page_number_format; "Layout": imposition, spreads, sheet_size, crop_marks, bleed; "Booklets": booklet_size, booklet_unit, booklet_folded, num_booklets, separate_covers; "Output": output, debug_grid. pad_with, extra_padding, creep_mm stay in the settings panel only.
- LAYOUTS = ("pages", "spreads", "booklets"); `layout_of(values)`; `with_layout(values, layout)` returns a copy.
- `field_enabled(values, name) -> bool`: page_number_* need page_numbers; sheet_size/crop_marks need layout != pages; bleed needs crop_marks; booklet_folded is forced on (disabled) when layout == booklets; page range needs layout == pages.
- `validate` uses settings_model.build_config plus pagerange.parse_page_range against len(build_plan(cfg)).
- `cli_args(values, page_range, defaults=None) -> list[str]`: only fields differing from defaults (settings_model.default_values()), flag names matching agenda/cli.py (bool -> --x/--no-x, booklet_folded -> --folded/--flat, output -> --output); `cli_command(...) -> str` joins with shlex.join prefixed "agenda-gen". Content fields outside EXPORT_FIELDS are represented by `--config <file>` only when a path is passed (keep simple: optional `config_path` arg).
- help_text EXPORT_HELP additions (short + detail): layout_pages, layout_spreads, layout_booklets, open_after, cli_preview, browse_output. Update TOOLTIPS["export_pdf"] to say it opens the export dialog.
Review: PASS

## Phase 05 — ExportDialog widget   [status: done]
Deliverable: agenda/gui/export_dialog.py: a QDialog with Page numbers / Layout / Booklets / Range & output groups, live validation, CLI-equivalent line, and tooltips on every control; not yet wired to the main window.
Files: agenda/gui/export_dialog.py (new), agenda/gui/style_model.py (only if a new objectName needs a rule), tests/test_gui_export_dialog.py (new)
Depends on: 04
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_gui_export_dialog.py` passes and the full suite passes. Tests: `ExportDialog(values, total_pages)` populates every control from values; changing controls makes `dialog.result_values()` return the edited values (only EXPORT_FIELDS changed, other keys untouched); choosing the "booklets" radio sets imposition True and disables the folded checkbox; an invalid combination (e.g. page range "2-3" with booklets, or booklet_size 3 with unit pages) disables the Export (OK) button and shows the error in `error_label`; every control listed in `dialog.controls` (dict name -> widget) has a non-empty toolTip or an ExpandingToolTip; `dialog.cli_line.text()` starts with "agenda-gen" and updates on change; `page_range()` and `open_after()` return the entered values.
Notes:
- Build editors from settings_model.field_specs() filtered by EXPORT_FIELDS (reuse the kinds; do not duplicate type logic). Layout is a QButtonGroup of three QRadioButtons (objectNames layout_pages/layout_spreads/layout_booklets) mapped through export_model.with_layout; imposition/spreads checkboxes are not shown separately.
- Output row: QLineEdit (objectName export_output) + "Browse..." button (QFileDialog.getSaveFileName; ensure_pdf on result). Range: QLineEdit page_range (placeholder "all"). Checkbox open_after.
- Tooltips: ExpandingToolTip(widget, *param texts) for Config fields (as SettingsPanel does), EXPORT_HELP texts for GUI-only controls. Apply export_model.field_enabled after every change.
- Buttons: QDialogButtonBox with an "Export" accept button and Cancel. No QSettings access inside the dialog (constructor args `open_after: bool`, `page_range: str`).
- Keep it Qt-free-logic-light: all rules come from export_model.
Review: PASS

## Phase 06 — Wire the dialog into MainWindow   [status: done]
Deliverable: "Export PDF" opens ExportDialog; accepting applies the export values to the settings (so preview, Save and the next dialog reflect them), exports with the page range in the background, remembers open-after-export and the last output directory in QSettings, and optionally opens the PDF.
Files: agenda/gui/app.py, agenda/gui/export_job.py, agenda/gui/settings_panel.py, tests/test_gui_export.py, tests/test_gui_export_flow.py (new)
Depends on: 05
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests that: monkeypatch ExportDialog.exec to accept with edited values (layout spreads, page_numbers on) and assert win.settings.values() contains them, win.wait_export() succeeds and the written PDF has landscape pages; page range "2-3" yields a 2-page PDF; open_after True calls a patched `MainWindow.open_file` with the output path; QSettings (a temp-file QSettings passed via `MainWindow(prefs=...)`) stores keys `export/open_after` and `export/last_dir`; cancelling the dialog starts no export; existing tests in tests/test_gui_export.py (start_export signature, GUI vs CLI parity) still pass unchanged.
Notes:
- `start_export(path, interactive=False, page_range: str = "")` keeps its current positional signature; ExportJob gets `pages: list[int] | None = None` passed to export_agenda(pages=...).
- Applying values: `settings.set_values({**settings.values(), **dialog.result_values()})` so `changed` fires once and the preview updates; then take cfg from settings.config(). Output path in the dialog defaults to EM.default_path(cfg), or last_dir + file name when last_dir pref exists.
- `MainWindow.open_file(path)` wraps QDesktopServices.openUrl(QUrl.fromLocalFile(path)); called from _on_export_done only for interactive exports with open_after.
- SettingsPanel: hide the editors (and their label rows) of export_model.EXPORT_FIELDS from the Global form but keep them in values()/set_values()/save_file round-trip (hidden widgets or a passthrough dict; values must be identical to before for save/load and tests/test_gui_settings.py). If a test asserts those editors are visible in the Global form, update it to assert they are absent and that values round-trip.
- Keep _sync_export_button behaviour (disabled reason appended when config invalid).
Review: PASS

## Phase 07 — Docs, sample config and parity tests   [status: done]
Deliverable: README and docs/architecture/gui.md describe the export dialog and every export option with its CLI flag; config.yaml shows the new options commented; a parametrized GUI-vs-CLI parity test covers each layout.
Files: README.md, docs/architecture/gui.md, config.yaml, tests/test_gui_export.py, tests/test_docs_export.py (new)
Depends on: 06
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including (a) tests/test_docs_export.py asserting README.md contains each CLI flag added in phases 01-03 (`--page-number-start`, `--page-number-first`, `--page-number-position`, `--page-number-placement`, `--page-number-format`, `--spreads`, `--sheet-size`, `--page-range`) and docs/architecture/gui.md mentions "ExportDialog", "export_model" and "export/open_after"; (b) a parametrized test over layouts pages/spreads/booklets exporting through MainWindow.start_export and through main(["--config", saved_yaml, ...]) giving equal _sig(); (c) tests/test_sample_files.py still green (new options in config.yaml only as comments).
Notes:
- README: new "### Export" subsection under "## Printing" (or "## GUI"): table of option -> CLI flag -> meaning, the page-range rule (single pages only), spreads vs booklets, sheet size, crop marks/bleed, page numbering format placeholders {n}/{total}. Update the GUI section: Export PDF opens a dialog; settings panel no longer shows export fields.
- gui.md: ExportDialog structure, export_model responsibilities, QSettings keys export/open_after and export/last_dir, data flow dialog -> settings.set_values -> ExportJob.
- Update docs/agent/STATE.md conventions only through the normal phase process.
Review: PASS

<!--
Planner findings (inventory for phases 08+, 2026-10-26):
- GUI appearance is ALREADY persisted only in QSettings (agenda/gui/app.py PREFS_KEY "appearance",
  style_model.APPEARANCES dark/light/system); it is NOT a Config field. But its control
  (SettingsPanel.appearance_box + appearance_changed signal) sits in the config panel's
  "Colors & styling" section (templates.STYLING, YAML block `style:`). That control moves out.
- No config.yaml in the repo carries GUI keys; Config is extra="forbid", so a stray `appearance:`
  key would currently fail. Phase 08 makes configfile drop it gracefully.
- Output styling today: Config.theme: str = "minimal" exists (CLI --theme, help text, YAML
  style.theme) but has NO effect; agenda/themes.py is an empty stub. Colors are the module-global
  tokens.COLORS (ink, muted, line, accent, tint, weekend_fill, holiday_fill) read at ~198 call
  sites in draw.py and agenda/pages/*.py (WEEKEND_STYLE/HOLIDAY_STYLE frozen at import). Fonts:
  only Inter (assets/fonts, 4 styles) registered in exporter.register_fonts as family "Inter";
  ~118 set_font("Inter", ...) literals across draw.py and pages/*.py.
- Previews render in worker threads (QThreadPool) -> the palette/fonts must travel with the FPDF
  object, never by mutating tokens.COLORS globally. render_cache keys on config_hash(cfg), so new
  Config fields invalidate previews automatically.
- Decisions: style fields stay FLAT in Config and live in the existing `style:` YAML block
  (templates.SECTIONS STYLING entry gains keys). `theme` stays `str` (existing files with any value
  keep loading); unknown names render as "minimal" and the CLI warns on stderr.
-->

## Phase 08 — GUI Settings dialog (appearance leaves the config panel)   [status: done]
Deliverable: a "Settings" menu in the main window with "Preferences..." opening a GuiSettingsDialog that holds the app appearance (dark/light/system); the appearance combo is gone from the configuration panel; legacy GUI keys in YAML are ignored with a warning instead of failing.
Files: agenda/gui/prefs_dialog.py (new), agenda/gui/app.py, agenda/gui/settings_panel.py, agenda/gui/help_text.py, agenda/configfile.py, tests/test_gui_style.py, tests/test_gui_prefs_dialog.py (new), tests/test_templates.py (or tests/test_configfile.py)
Depends on: none
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests that: (a) `MainWindow(prefs=tmp_qsettings).menuBar()` has a menu titled "Settings" (or "&Settings") whose actions include one with objectName "action_preferences"; (b) `SettingsPanel` has no attribute `appearance_box` and no widget with objectName "appearance" is a descendant of win.settings; (c) `GuiSettingsDialog(appearance="dark")` exposes `appearance_box` (objectName "appearance") with items == list(style_model.APPEARANCES), a non-empty toolTip/ExpandingToolTip, and `appearance()` returns the chosen value; (d) accepting the dialog (monkeypatch exec to set "light" and accept) via `win.open_preferences()` sets `win.appearance == "light"`, stores QSettings key "appearance" == "light", and win.settings.values() is unchanged; cancelling changes nothing; (e) a new MainWindow with the same prefs starts with appearance "light"; (f) `configfile.load_yaml` on a file containing `appearance: dark` (top level) or `style: {appearance: dark, theme: minimal}` returns the same dict as without that key and emits a `warnings.warn` (UserWarning) mentioning "appearance" and "GUI Settings".
Notes:
- prefs_dialog.py: `GuiSettingsDialog(QDialog)` with ctor `(appearance: str, parent=None)`, a QFormLayout row "Appearance" + QDialogButtonBox OK/Cancel. No QSettings access inside the dialog (app.py reads/writes, as with ExportDialog). Applying is live on accept only.
- app.py: build a QMenuBar (`self.menuBar()` if MainWindow is a QMainWindow, else a QMenuBar added at the top of the layout; check which). Action text "Preferences...", shortcut QKeySequence.StandardKey.Preferences, objectName "action_preferences", connected to `open_preferences()`. Reuse the existing `_set_appearance` for apply + persist. Keep PREFS_KEY "appearance" so saved choices survive.
- settings_panel.py: delete appearance_box, appearance_tooltip, appearance_changed and the STYLING-row insertion; drop the APPEARANCES/DEFAULT_APPEARANCE import. Remove the corresponding wiring in app.py.
- help_text: keep TOOLTIPS["appearance"] (used by the dialog); add TOOLTIPS["preferences"] for the menu action ("GUI look; does not change the PDF").
- configfile: `LEGACY_GUI_KEYS = ("appearance",)` dropped both at top level and inside the `style:` block before flattening, with one UserWarning per key. Nothing else changes in loading.
- Update tests/test_gui_style.py tests that used `win.settings.appearance_box` to use the dialog instead (same assertions about persistence).
Review: PASS

## Phase 09 — Output palettes threaded through rendering   [status: done]
Deliverable: agenda/themes.py defines named output palettes; the selected `cfg.theme` palette travels with each FPDF document and every page/draw helper reads colors from it instead of the global tokens.COLORS; the default ("minimal") output is unchanged.
Files: agenda/themes.py, agenda/exporter.py, agenda/draw.py, agenda/pages/base.py, agenda/pages/core.py, agenda/pages/optional.py, agenda/pages/value_added.py, agenda/cli.py, tests/test_themes.py (new), tests/data/default_style_fingerprint.json (new)
Depends on: none
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests/test_themes.py which checks: (a) the default-SMALL fingerprint (sha256 per page of pypdf `page.get_contents().get_data()` for `{"year": 2026, "planners": ["weekly"], "daily_months": []}`) equals tests/data/default_style_fingerprint.json, which MUST be generated by a script run on the code BEFORE this phase's refactor (commit it as the first step); (b) `themes.THEMES` keys == ("minimal", "mono", "ocean", "forest") in that order, every palette has exactly the keys of tokens.COLORS, and THEMES["minimal"] == tokens.COLORS; (c) for every palette, `agenda.gui.style_model.contrast_ratio` against white is >= 7 for ink, >= 4.5 for muted and accent; (d) exporting SMALL with theme="ocean" gives different content streams than minimal but identical page count and extracted text; (e) theme="nonexistent" exports identically to minimal and `main([... "--theme", "nonexistent"])` exits 0 with a stderr warning containing "unknown theme"; (f) `grep -rn "tokens.COLORS\[" agenda/draw.py agenda/pages` returns nothing (test via reading the files).
Notes:
- themes.py (Qt-free, no Config import at runtime): `Palette = dict[str, tuple[int,int,int]]`; `THEMES: dict[str, Palette]` ("minimal" = copy of tokens.COLORS; "mono" = grayscale accent; "ocean" blue accent; "forest" green accent; fills light tints of the accent); `palette_for(theme: str, overrides: dict[str, tuple] | None = None) -> Palette` (unknown -> minimal); `is_known(theme) -> bool`.
- Carry the palette on the document: in exporter.new_document set `pdf.agenda_palette = themes.palette_for(cfg.theme)` (phase 10 adds overrides); add `draw.color(pdf, name) -> tuple` reading `getattr(pdf, "agenda_palette", tokens.COLORS)`. Replace every `tokens.COLORS["x"]` in draw.py/pages with `color(pdf, "x")` (helpers already receive pdf). Replace module constants WEEKEND_STYLE/HOLIDAY_STYLE by `weekend_style(pdf)`/`holiday_style(pdf)` or build them inside day_style_for from a palette arg; keep names importable if tests import them (check with grep in tests/).
- Do NOT mutate tokens.COLORS (worker threads render previews concurrently). Debug-grid colors (_INNER_FILL etc.) are tooling, not output style: leave them.
- CLI: after Config validation, `if not themes.is_known(cfg.theme)`: print warning to stderr, continue. Update help_text PARAM_DETAILS["theme"] to list the four names.
- Mechanical but large: if the diff exceeds ~10 files it is still one phase (same edit everywhere); do not change layout, sizes or strokes.
Review: PASS

## Phase 10 — Per-color overrides (Config, YAML, CLI)   [status: done]
Deliverable: optional Config fields override individual palette colors on top of the theme; they live in the `style:` YAML block, have CLI flags and help texts, and change the exported PDF and previews.
Files: agenda/config.py, agenda/themes.py, agenda/exporter.py, agenda/templates.py, agenda/cli.py, agenda/gui/help_text.py, tests/test_themes.py, tests/test_config.py, tests/test_cli.py, tests/test_templates.py
Depends on: 09
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests that: (a) Config(color_accent="#1E6FD9").color_accent == "#1e6fd9", "1e6fd9" and "#abc" are normalised to "#1e6fd9"/"#aabbcc", "blue"/"#12345g" raise ValueError naming the field; (b) all seven fields default to None and Config() equals the pre-phase Config() on every old field (tests/test_sample_files.py green); (c) exporting SMALL with color_accent set to minimal's own accent hex is byte-identical in content streams to the default export, while color_accent="#0000ff" changes them; (d) YAML `style: {theme: ocean, accent: "#0000ff"}` loads to the same Config as flat `theme: ocean` + `color_accent: "#0000ff"` and settings_model.save_yaml round-trips it; (e) `main([... "--color-accent", "#0000ff", "--color-ink", "#111111"])` exits 0 and `--color-accent nope` exits 2.
Notes:
- Fields (Look & output block, after theme): `color_ink`, `color_muted`, `color_line`, `color_accent`, `color_tint`, `color_weekend_fill`, `color_holiday_fill`, each `str | None = None`. One shared field_validator: strip, accept "#rgb"/"#rrggbb" with or without "#", return lowercase "#rrggbb"; else ValueError "<field> must be a hex color like #c85028".
- themes.py: `hex_to_rgb`, `rgb_to_hex`; `palette_for(theme, overrides)` already exists; exporter builds overrides from the non-None color_* fields (`{name.removeprefix("color_"): hex_to_rgb(v)}`).
- templates.py STYLING fields become {"theme": "theme", "ink": "color_ink", "muted": "color_muted", "line": "color_line", "accent": "color_accent", "tint": "color_tint", "weekend_fill": "color_weekend_fill", "holiday_fill": "color_holiday_fill"}. The settings panel will show them automatically as text editors (proper color editors come in phase 12); fix tests/test_templates.py expectations accordingly.
- CLI: `--color-ink` ... `--color-holiday-fill` (str options) through build_overrides. help_text PARAM_SHORT/PARAM_DETAILS for all seven (tests/test_gui_param_help.py requires them): say "empty = use the theme's color" and name the elements affected (accent: month titles, holidays; line: rules and dots; etc.).
- None values must not be written to YAML by save_yaml if the existing save logic omits defaults; check and keep consistent.
Review: PASS

## Phase 11 — Primary and secondary fonts   [status: done]
Deliverable: Config fields `font_primary` (headings, titles, bold text) and `font_secondary` (body, labels, numbers) select the PDF fonts: the bundled "inter" or a user .ttf/.otf file; used by export and previews, with CLI flags, YAML `style:` keys and help texts. Default output unchanged.
Files: agenda/fonts.py (new, Qt-free), agenda/config.py, agenda/exporter.py, agenda/draw.py, agenda/pages/core.py, agenda/pages/optional.py, agenda/pages/value_added.py, agenda/templates.py, agenda/cli.py, agenda/gui/help_text.py, tests/test_fonts.py (new)
Depends on: 10
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests/test_fonts.py: (a) the default-SMALL fingerprint test from phase 09 still passes (same tests/data file) and the default PDF embeds only Inter fonts (pypdf: every /BaseFont contains "Inter"); (b) `fonts.resolve("inter")` returns the 4 Inter files; `fonts.resolve(path_to_Inter-Regular.ttf_copied_to_tmp_as_MyFont-Regular.ttf)` finds the sibling styles when copied too and falls back to the regular file for missing styles; `fonts.resolve("nope")` and a missing path raise ValueError; (c) Config(font_primary="nope") raises ValueError naming font_primary; (d) exporting SMALL with font_primary set to a tmp copy "MyFont-Regular.ttf" (+ "MyFont-Bold.ttf") yields a PDF whose /BaseFont names include "MyFont" and still "Inter" (secondary) and identical extracted text; (e) `main([... "--font-primary", <tmp path>, "--font-secondary", "inter"])` exits 0, `--font-primary nope` exits 2; (f) no `set_font("Inter"` literal remains in agenda/draw.py or agenda/pages (test reads files).
Notes:
- fonts.py: `BUILTIN = {"inter": FONT_DIR/Inter-*.ttf}` (move FONT_DIR/FONT_FILES from exporter, keep exporter names importable as aliases); `resolve(spec: str) -> dict[style, Path]` for styles "", "B", "I", "BI": built-in name (case-insensitive) or a path to a .ttf/.otf; siblings found by replacing "Regular" in the stem with "Bold"/"Italic"/"BoldItalic" (also "-Regular" absent -> try "<stem>-Bold"); missing styles fall back to the regular file.
- Config: `font_primary: str = "inter"`, `font_secondary: str = "inter"` (Look & output, after colors); validator calls fonts.resolve (lazy import) and stores the stripped string; built-in names lowercased.
- Rendering: new_document registers each DISTINCT resolved font set once under family "Inter" (if built-in inter) or "AgendaPrimary"/"AgendaSecondary", and sets `pdf.agenda_fonts = {"primary": family, "secondary": family}`; when both roles resolve to the same files they share ONE family (keeps default output byte-identical: register Inter exactly as today). Add `draw.font(pdf, role) -> str` (default "Inter" when attribute missing). Replace call sites mechanically: style containing "B" -> "primary", otherwise "secondary".
- Missing glyphs: fpdf2 substitutes/raises per its config; do not add fallback logic beyond what fpdf2 offers (no new deps). Note in help text that the font must contain the agenda language's characters.
- templates STYLING gains "primary_font": "font_primary", "secondary_font": "font_secondary". CLI `--font-primary`, `--font-secondary`. PARAM_SHORT/DETAILS for both.
- font paths in YAML are stored as given (relative paths resolve against the CWD, same as daily_quotes_file; check how those are handled and match it).
Review: PASS

## Phase 12 — Output-style editors in the "Colors & styling" panel   [status: done]
Deliverable: the configuration panel's "Colors & styling" section (renamed "PDF colors & fonts") edits the generated file's style with proper widgets: theme combo of known palettes, color fields with swatch + QColorDialog and a "theme default" clear, font fields with a built-in choice + Browse for a font file; the preview updates on change.
Files: agenda/gui/settings_model.py, agenda/gui/settings_panel.py, agenda/gui/style_editors.py (new), agenda/gui/help_text.py, agenda/templates.py, tests/test_gui_style_editors.py (new), tests/test_gui_settings.py, tests/test_gui_settings_model.py (or the existing settings model test)
Depends on: 08, 11
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including tests that: (a) settings_model.field_specs() gives kind "theme" for theme with choices == tuple(themes.THEMES), kind "color" for all seven color_* fields and kind "font" for font_primary/font_secondary (Qt-free test); (b) in a SettingsPanel, editors for those fields are descendants of sections[T.STYLING], each has an ExpandingToolTip, and the section label is "PDF colors & fonts"; (c) setting a color editor's value to "#0000ff" (via its public `set_value`, simulating the dialog result) makes `panel.values()["color_accent"] == "#0000ff"` and `changed` fires once; its clear button sets the value to None; the swatch button's background reflects the effective color (theme color when None); (d) set_values with theme="legacy-name" shows that name as an extra combo item and values() returns it unchanged; (e) font editor: choosing "inter" yields "inter"; set_value(tmp font path) round-trips; (f) values() -> save_yaml -> load round-trip equals the input for a style-heavy config; (g) no widget in the panel has objectName "appearance".
Notes:
- settings_model: extend `_SPECIAL` with "theme": THEME, color_* : COLOR, font_*: FONT (new kind constants, added to the kinds tuple); FieldSpec.choices for THEME = tuple(themes.THEMES).
- style_editors.py: `ColorEdit(QWidget)` (QLineEdit + swatch QToolButton opening QColorDialog.getColor + "x" clear button; `value()`/`set_value()`/`edited` signal; invalid text shown via the panel's normal Config error path); `FontEdit(QWidget)` (editable QComboBox with fonts.BUILTIN names + "Browse..." QFileDialog filter "Fonts (*.ttf *.otf)"). Keep QColorDialog/QFileDialog calls in small methods so tests monkeypatch them.
- SettingsPanel._make/_set/_get gain branches for the three kinds; empty color text -> None.
- Swatch effective color: themes.palette_for(current theme)[name] when the field is None (refresh on theme change).
- templates STYLING label -> "PDF colors & fonts"; key/block names unchanged (YAML `style:` stays).
- help_text: TOOLTIPS for the swatch/clear/browse buttons; mention in the section help that the app appearance is under Settings > Preferences.
Review: PASS

## Phase 13 — Docs, sample config and style parity tests   [status: done]
Deliverable: README and docs/architecture/gui.md describe the GUI Settings dialog vs. the PDF style options (themes, colors, fonts) with their YAML keys and CLI flags; config.yaml shows the `style:` block commented; GUI-vs-CLI parity covers a styled export.
Files: README.md, docs/architecture/gui.md, docs/architecture/layout-grid.md, config.yaml, tests/test_docs_style.py (new), tests/test_gui_export.py
Depends on: 12
Done when: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` passes, including (a) tests/test_docs_style.py asserting README.md contains every flag `--theme`, `--color-ink`, `--color-muted`, `--color-line`, `--color-accent`, `--color-tint`, `--color-weekend-fill`, `--color-holiday-fill`, `--font-primary`, `--font-secondary`, each theme name in themes.THEMES, and "Preferences"; docs/architecture/gui.md mentions "GuiSettingsDialog", "ColorEdit", "FontEdit" and states appearance is stored in QSettings key "appearance"; (b) a parity test exporting through MainWindow.start_export with theme "ocean", color_accent "#0000ff" and font_primary a tmp font copy equals main(["--config", saved_yaml, ...]) by _sig(); (c) tests/test_sample_files.py stays green (new style keys in config.yaml only as comments).
Notes:
- README: replace the `style: {theme: minimal}` example with the full commented block; new "### PDF style" subsection (table: YAML key -> Config field -> CLI flag -> meaning; theme list; color format; font spec rules and fallback for missing styles; font licensing reminder for user fonts); update the GUI section: appearance lives in Settings > Preferences and never affects the PDF.
- layout-grid.md: say colors come from themes.py palettes carried on the document (no global mutation).
- gui.md: prefs_dialog, style_editors, data flow panel -> Config -> new_document palette/fonts.
Review: PASS

## Open questions
- DECIDED: creep_mm stays untouched and out of the dialog (not implemented; revisit in a later plan).
- DECIDED: page-number placement is configurable (`page_number_placement`: margin (default) or footer).
- Bundled fonts: only Inter ships today. Recommended default: bundle no new fonts; offer "inter" plus any user .ttf/.otf path (phase 11). If you want built-in alternatives (e.g. a serif such as Source Serif 4 and a mono, both OFL), say which and they become extra fonts.BUILTIN entries.
- Built-in palettes: recommended minimal (current look), mono, ocean, forest (phase 09). Rename or add others if you prefer.
- Font roles: recommended rule primary = headings/bold text, secondary = body/regular text. Say if you want e.g. day/date numbers on the primary font instead.
- Unknown `theme` values keep loading and render as minimal with a CLI warning (to honour "existing config.yaml keeps loading"); say if you prefer a hard error.
