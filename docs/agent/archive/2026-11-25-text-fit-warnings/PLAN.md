# PLAN: Header/footer text fit option and cut-text warnings

Plan: 2026-11-25-text-fit-warnings
Closed: 2026-11-26
Goal: Let the user choose how page header and footer text that is too long for its band is fitted (header: overflow (default, as today), ellipsis, shrink, wrap; footer: ellipsis (default), shrink, wrap), and report every cut with the exact agenda pages and region in the CLI, the GUI export result and the preview; also make the back cover optional (off by default) and give the Daily page's Schedule/Priorities/Notes titles a top margin.
Backlog: -
Out of scope: text inside the content area (weekly day-row holiday labels, value-added `_fit` labels, contacts/notes rows); the page-number label (short, fixed format); the AgendaPDF.cell scale>1 safety net for non-header/footer text (stays silent); translating the assembler summary/--dry-run (separate backlog item); fixing the footer quote/extra overlap bug (separate backlog item); a non-zero exit code on cuts
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

Phases are written by the phase-planner agent, one block per phase:

## Phase 01 — <short title>   [status: …]
Deliverable: <what exists when done>
Files: <paths likely created/changed>
Depends on: none
Done when: <Verify command> passes, and <objective check for this phase>
Notes: <decisions, pitfalls>
Review: -

Status values: pending | in-progress | done | blocked
The Review line is filled in by run-plan: PASS, or FAIL -> fixed -> PASS.
Only the run-plan orchestrator changes status tags. You can edit them by hand
(e.g. set a blocked phase back to pending after answering its question).
-->

<!--
Findings (2026-11-25, planner):
- Footer: only Daily._footer (agenda/pages/core.py ~443) draws footer text: the daily phrase
  (left, italic, size * daily_quotes_size/100) and the dated extra text (right); each half-width
  when both exist; both cut with day_extras.truncate (ellipsis). Footer band = tokens.FOOTER_HEIGHT 6 mm.
- Header: ~30 sites draw a single-line title with pdf.cell(h.w, h.h, title) in g.header
  (core.py: Yearly, Monthly, Weekly._page, Daily, Notes, Contacts; 10 agenda/pages/optional/*.py;
  value_added/_common._Counted._header + 12 value_added/*.py with their own `h = g.header`).
  With font scale 1 an over-long title just overflows the band (no cut); with a font scale > 1
  AgendaPDF.cell (agenda/pdfdoc.py) silently truncates with "…". Daily header also truncates the
  holiday name (truncate) next to "Week N", and drops it when only "…" would remain.
  Header band = tokens.HEADER_HEIGHT 12 mm (room for 2 lines of the 12 pt title at a smaller size).
- Page numbers: draw() gets no page number. exporter._render_plan knows entry.page_number (real
  1-based agenda page) when it calls add_page; Weekly draws its left page via switch_page, so
  pdf.page at draw time identifies the document page. A doc-page -> agenda-page map on AgendaPDF
  gives the exact agenda page for partial renders (render_pages) too.
- Config fields drive CLI flags and tooltips (ADR 0001; json_schema_extra "detail" + "cli");
  Spanish field texts in agenda/uitext/es_fields.py; tests/data/param_help.json and
  tests/test_cli_flags.py tables list every field. YAML/GUI section placement in
  agenda/templates.py SECTIONS (ADR 0004); the "PDF colors & fonts" (STYLING, yaml "style:") section fits.
- export_agenda/render_pages return Path/bytes; keep that (public API stable) and add an optional
  keyword collector instead. Existing summary warnings: assembler.PlanSummary.warnings (English).
-->

## Phase 01 — Qt-free text-fit engine and cut log   [status: done]
Deliverable: New module agenda/textfit.py (no fpdf, no PySide6 imports) with: `FIT_MODES = ("overflow", "ellipsis", "shrink", "wrap")` (plus `FOOTER_FIT_MODES = ("ellipsis", "shrink", "wrap")`); `fit_text(text, width, height, size_pt, mode, width_of, line_height_of, min_scale=0.6, max_lines=2) -> FitResult` where FitResult has `lines: tuple[str, ...]`, `size_pt: float`, `cut: bool`; and a `CutLog` collector with `add(page: int, region: str, text: str)`, `entries` (sorted by page), `pages(region=None) -> list[int]`, `__bool__`, and `format_ranges(pages) -> str` ("3, 5, 14-20"). overflow = one line, text and size unchanged, cut=False always (even when wider than the width). ellipsis = one line, day_extras.truncate semantics (reuse it), cut when shortened. shrink = largest size in [size_pt*min_scale, size_pt] (step 0.25 pt or binary search) that fits on one line; if even the minimum does not fit, ellipsis at the minimum size and cut=True. wrap = word-wrap into at most max_lines lines that fit `height` (line_height_of(size) * n <= height, reducing size down to min_scale if 2 lines do not fit the height); a single word wider than the width is broken by characters; text left over after the last line is cut with "…" on the last line, cut=True.
Files: agenda/textfit.py, tests/test_textfit.py
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests/test_textfit.py (using a fake width_of such as `lambda s: len(s)`) covers: fitting text unchanged with cut=False in every mode; overflow returning over-long text unchanged at the same size with cut=False; ellipsis output equal to day_extras.truncate; shrink returning a smaller size without cut, and cut=True below min_scale; wrap producing 2 lines without cut, and cut=True with "…" when 3 lines would be needed; CutLog.pages()/format_ranges ("1, 3-5") and region filtering; and `python -c "import agenda.textfit, sys; assert 'PySide6' not in sys.modules and 'fpdf' not in sys.modules"` succeeds.
Notes: Keep the module pure so the GUI and CLI can format its data. Do not change day_extras.truncate or _common._fit. Region names are stable ids: "header", "footer" (UI text comes later through tr()).
Review: PASS

## Phase 02 — header_text_fit / footer_text_fit options (config, CLI, GUI tooltip)   [status: done]
Deliverable: Two Config fields: `header_text_fit: Literal["overflow", "ellipsis", "shrink", "wrap"] = "overflow"` and `footer_text_fit: Literal["ellipsis", "shrink", "wrap"] = "ellipsis"` (both defaults reproduce today's output), each with description + detail (json_schema_extra "detail", "cli": {"type": "str"}) so the CLI flags --header-text-fit / --footer-text-fit and GUI tooltips come from the field (ADR 0001). Spanish texts in agenda/uitext/es_fields.py. Placed in the STYLING section of agenda/templates.py (yaml keys under `style:`, e.g. "header_text_fit"/"footer_text_fit") so they show in the "PDF colors & fonts" tab. Commented example lines in config.yaml. README option list updated. The options are stored but not yet used by the renderer (phases 03, 05-07).
Files: agenda/config.py, agenda/templates.py, agenda/uitext/es_fields.py, config.yaml, README.md, tests/data/param_help.json, tests/test_cli_flags.py, tests/test_text_fit_options.py
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests/test_text_fit_options.py asserts: Config().header_text_fit == "overflow" and Config().footer_text_fit == "ellipsis"; loading the repo config.yaml gives the same Config as before (both fields default); `agenda-gen --header-text-fit wrap --footer-text-fit shrink --dry-run` (via cli.main) exits 0, an invalid value exits 2, and `--footer-text-fit overflow` exits 2 (overflow is header-only); a `style:` YAML block with header_text_fit: shrink loads to Config.header_text_fit == "shrink"; and the GUI settings widget for each field has a non-empty tooltip in English and Spanish (gui-marked test, MainWindow closed after wait_idle()).
Notes: Separate fields (user decision 2026-11-25): the header gets a fourth value "overflow", the default, which keeps today's behaviour (a too-long title runs into the margin; with a font scale > 1 the existing AgendaPDF.cell safety net still shortens it silently) and is never reported as a cut. The footer has no "overflow" value; its default "ellipsis" = current output. Detail text must say: "overflow" (header only, default) draws the title unchanged even past the band and never warns; "ellipsis" shortens with "…", "shrink" lowers the font size down to 60 % then shortens, "wrap" uses up to 2 lines then shortens; text shortened under ellipsis/shrink/wrap is reported with its pages after export. Keep test_cli_flags and param_help.json in sync the same way the existing fields are listed.
Review: PASS

## Phase 03 — Renderer plumbing and footer fitting with cut logging   [status: done]
Deliverable: AgendaPDF gains `agenda_page_numbers: dict[int, int]` (document page -> real agenda page, filled by exporter.add_page/_render_plan from entry.page_number) and `agenda_cut_log: CutLog | None`. A helper in agenda/draw.py, e.g. `fit_cell(pdf, x, y, w, h, text, *, region, mode, role, style, size_pt, align="L")`, measures with pdf.get_string_width under the given font, calls textfit.fit_text, draws the resulting line(s) (vertically centered in h), restores nothing else; for mode "overflow" it makes exactly today's single `pdf.cell(w, h, text, align=...)` call (same stream, safety net included) and never logs; and on cut adds (agenda_page_numbers.get(pdf.page, pdf.page), region, original text) to agenda_cut_log when set. Daily._footer uses it for the phrase and the extra text with mode=config.footer_text_fit, region "footer". `export_agenda(..., cuts: CutLog | None = None)` and `render_pages(..., cuts: CutLog | None = None)` (keyword, optional; return types unchanged) attach the log to the document; with `pages=` the log holds only the rendered pages' cuts, still numbered as agenda pages.
Files: agenda/pdfdoc.py, agenda/draw.py, agenda/exporter.py, agenda/pages/core.py, tests/test_text_fit_footer.py
Depends on: 01, 02
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests/test_text_fit_footer.py shows: with a daily_quotes_file whose phrase for one date is very long, export_agenda(cfg, path, cuts=log) under footer_text_fit="ellipsis" logs exactly the agenda page numbers of those day pages (cross-checked against build_plan) with region "footer", and the PDF text of that page contains "…"; under "wrap" a moderately long phrase is drawn on 2 lines (two text runs/y positions on that page, via pypdf) and is not logged; under "shrink" it is drawn without "…" and not logged; render_pages(cfg, plan, [i], cuts=log) logs the same agenda page number as the full export; and with default config and short phrases the existing export/render_pages stream-equality tests still pass unchanged.
Notes: Measure under the actual font (set_font applies agenda_font_scale), so shrink/wrap work on the scaled size. Keep footer half-width split as today. With cuts=None nothing is collected (no overhead beyond a None check). Phase 04 surfaces the log; phases 05-07 reuse fit_cell for headers.
Review: PASS

## Phase 04 — Report cuts in the CLI and after GUI export   [status: done]
Deliverable: Qt-free formatting in agenda/textfit.py or a new agenda/cutreport.py: `cut_report_lines(log) -> list[str]` built with agenda.uitext.tr(): one summary line per region ("Header text was shortened on 3 pages: 5, 9, 14-20") followed by one line per distinct cut text with its pages (text shown up to 60 characters). New uitext keys in en.py and es.py (plural forms like the existing summary.* keys). CLI: run() passes a CutLog to export_agenda and, when non-empty, echoes the lines to stderr after "Wrote …" (exit code stays 0). GUI: ExportJob passes a CutLog; ExportSignals.done carries the report text (or a new `cuts` signal); MainWindow._on_export_done shows the export result plus the report: status text gets a short "⚠ N pages with shortened text" suffix and the interactive message box uses QMessageBox.warning with the full report as detailed text; `export_result` keeps the full text for tests.
Files: agenda/cutreport.py (or agenda/textfit.py), agenda/uitext/en.py, agenda/uitext/es.py, agenda/cli.py, agenda/gui/export_job.py, agenda/gui/app.py, tests/test_cut_report.py, tests/test_cli.py, tests/test_gui_export.py
Depends on: 03
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and: tests/test_cut_report.py (no PySide6) checks the English and Spanish lines for a hand-built CutLog including the exact page list "5, 9, 14-20"; a CLI test with a long-phrase config (small daily_months range) asserts stderr contains the footer summary line with the expected agenda page numbers and exit code 0, and a no-cut export prints no such line; a gui-marked test runs start_export + wait_export on the same config and asserts window.export_result contains the page list (window closed after wait_idle()); tests/test_ui_strings_lint.py passes with the new keys.
Notes: All user-visible text through tr() (ADR 0005/0007), never agenda/i18n.py. Page numbers are agenda page numbers (as printed by --list and the preview); with imposition/spreads say "agenda page" in the text so it is not read as a sheet number. Do not touch the English assembler summary.
Review: PASS

## Phase 05 — Fit core page headers (incl. Daily holiday)   [status: done]
Deliverable: A `draw_header_title(pdf, g, text, config, size_pt, align="L")` (or similar) helper in agenda/draw.py built on fit_cell with region "header" and mode=config.header_text_fit. Yearly, Monthly, Weekly._page, Daily, Notes and Contacts headers use it. Under "overflow" (default) every header, including the Daily holiday handling (truncate, dropped when only "…" is left), draws exactly as today; nothing is logged except the Daily holiday name, which is already cut today and is logged as a header cut (with its page) whenever it is shortened or dropped, under every mode including "overflow". Under ellipsis/shrink/wrap, Daily's left title and right "holiday · Week N" part are fitted so they never overlap: the title is fitted first in the header width minus the right label's width; the holiday name is shortened (ellipsis or shrink per mode) and logged as a header cut when shortened or dropped because of space.
Files: agenda/draw.py, agenda/pages/core.py, tests/test_text_fit_header.py
Depends on: 03
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests/test_text_fit_header.py shows: on a narrow page size (smallest supported) with font_primary_size at its maximum, the weekly right-page title spanning two months is logged as region "header" with the exact agenda page under "ellipsis", is drawn on 2 lines and not logged under "wrap" (or logged only if 2 lines do not fit), and is not cut under "shrink" when 60 % fits; a Daily page with a long holiday name logs its page under "ellipsis"; with the default header_text_fit ("overflow") the same narrow/large-font config logs no header cut other than Daily holiday-name cuts (a long holiday name logs its page under "overflow" too) and its weekly/daily page content streams equal those produced by a plain `pdf.cell` draw (output unchanged vs. before this phase); and at default size on A5 no header cut is logged for a full default export under "ellipsis" either.
Notes: Default "overflow" must give byte-identical pages, and a title that fits must render exactly as before in every mode (same x/y/size), so existing stream-equality tests stay green. The AgendaPDF.cell safety net stays as a fallback; fit_cell fits first, so the safety net does not fire for header text.
Review: PASS

## Phase 06 — Fit optional page headers   [status: done]
Deliverable: The 10 optional pages draw their `g.header` title through draw_header_title (mechanical replacement of the set_font + set_xy + cell triple), so header_text_fit applies and cuts are logged.
Files: agenda/pages/optional/budget.py, goals.py, habits.py, holidays.py, important_dates.py, monthly_review.py, passwords.py, projects.py, schedule.py, todo.py, tests/test_text_fit_header.py
Depends on: 05
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and `grep -n "cell(h.w, h.h" agenda/pages/optional/*.py` prints nothing, and a parametrized test over the optional page ids, with a forced over-long title (monkeypatched Strings lookup or the largest font scale on the smallest page), logs the page's agenda page number with region "header" under header_text_fit="ellipsis" and logs nothing under the default "overflow".
Notes: Keep each page's font size and color; only the drawing call changes. Under the default "overflow" the output must stay identical to today.
Review: PASS

## Phase 07 — Fit value-added page headers   [status: done]
Deliverable: value_added/_common._Counted._header and the 12 value-added pages with their own `h = g.header` title use draw_header_title.
Files: agenda/pages/value_added/_common.py, challenge30.py, extras_guide.py, gratitude.py, health.py, idea_map.py, meals.py, media.py, monthly_quotes.py, qr_codes.py, travel.py, vision_board.py, tests/test_text_fit_header.py
Depends on: 05
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and `grep -n "cell(h.w, h.h\|cell(g.header.w" agenda/pages/value_added/*.py` prints nothing, and a parametrized test over the value-added page ids (same forcing technique as phase 06) logs each page's agenda page number with region "header" under header_text_fit="ellipsis" and logs nothing under the default "overflow".
Notes: Mechanical change, about 13 files with 2-4 lines each. Under the default "overflow" the output must stay identical to today. Content-area labels (_fit, _label) are out of scope.
Review: PASS

## Phase 08 — Show cut warnings in the preview   [status: done]
Deliverable: The preview render worker passes a CutLog to render_pages and emits it with the images; a Qt-free helper in agenda/gui/preview_model.py maps the log to the warning text for a given plan index (via tr()); the preview shows it for the current page (e.g. a warning label or the page-indicator tooltip with "⚠"), and the summary strip tooltip lists the pages seen so far. Nothing is shown for pages without cuts.
Files: agenda/gui/workers.py, agenda/gui/preview.py, agenda/gui/preview_model.py, agenda/uitext/en.py, agenda/uitext/es.py, tests/test_gui_preview_model.py, tests/test_gui_preview.py
Depends on: 04, 05
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and a Qt-free test checks the preview_model helper returns the header/footer text for an index in the log and "" otherwise; a gui-marked test opens MainWindow with a long-phrase config, navigates the preview to an affected day page, wait_idle()s, and asserts the warning widget/tooltip text names that page, then close()s the window.
Notes: Preview only knows the pages it rendered; the full list comes from export (phase 04). Keep the worker's existing signal signature compatible or update every connect site in the same phase.
Review: PASS

<!--
Findings (2026-11-26, planner, phases 09-10):
- Back cover: build_plan (agenda/assembler.py ~182-356) always appends BackCover in try_padding
  (~306-320); with separate_covers a blank inside-back filler (section front_back) precedes it and
  `inner_end = len(entries) - 2 if sep else len(entries)` (~344) assumes both exist. summarize()
  derives cover_pages from booklet_index, so it needs no change. `back_cover` in Config.pages is
  ignored by build_plan today (core ids are; _extras only reads optional/value_added), and the
  repo config.yaml / tests/test_sample_files.py PAGES list it.
- separate_covers is an export-dialog field (agenda/gui/export_model.py "booklets" group), not
  in SECTIONS; unlisted fields fall into GLOBAL (templates.group_of) = "Whole agenda" tab.
- Help texts naming the back cover: config.py separate_covers (~189) and extra_padding (~575),
  es_fields.py separate_covers (~79) and extra_padding (~268), param_help.json lines 87/115,
  uitext en.py/es.py "section_desc.front_back", README.md ~204/~259.
- Daily titles: Daily._label (core.py ~525) draws the label cell at g.row(row) with height
  g.baseline. Schedule (row 0) and Priorities (row 0) start right at content.y = header band
  bottom; Notes (row g.rows // 2) starts exactly on the last Priorities write-in line g.row(half).
  Below each label: Schedule's first hour label sits at g.row(1); Priorities/Notes' first write-in
  line at g.row(r0 + 2). Monthly's "priorities" label already has a gap row (n0 = 1 + grid_rows + 1).
-->

## Phase 09 — Back cover optional, off by default   [status: done]
Deliverable: New Config field `back_cover: bool = False` (description "Add a back cover page at the end." + json_schema_extra "detail" + `"cli": {}` so --back-cover/--no-back-cover and the GUI tooltip come from the field, ADR 0001). build_plan appends BackCover only when config.back_cover is true; with it off the plan ends with the padding (or the last back-matter page). Spanish field text in agenda/uitext/es_fields.py; tests/data/param_help.json and tests/test_cli_flags.py list the field like separate_covers; help texts that mention the back cover are updated to say "when back_cover is on". Commented example line `# back_cover: false` in config.yaml's "Other options" block; README option list updated.
Files: agenda/config.py, agenda/assembler.py, agenda/uitext/es_fields.py, agenda/uitext/en.py, agenda/uitext/es.py, config.yaml, README.md, tests/data/param_help.json, tests/test_cli_flags.py, tests/test_back_cover.py, tests/test_padding.py, tests/test_build_plan.py, tests/test_plan_cases.py, tests/test_summary.py
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests assert: Config().back_cover is False; build_plan(Config(year=2026)) contains no BackCover entry and its length is still a multiple of pages_per_booklet; with back_cover=True the last entry is BackCover (today's plan, existing padding tests run with back_cover=True); with separate_covers=True and back_cover=False the plan has exactly 2 entries with booklet_index None (cover + inside-cover filler), no trailing blank filler, the last entry has a booklet_index, the inner block starts at page 3 on a right page and its length is a multiple of the booklet size (and of 4 when folded); with separate_covers=True and back_cover=True the existing _check_sep checks (4 outside pages) still hold; summarize(...).cover_pages is 2 resp. 4 for those two cases; `cli.main(["--back-cover", "--dry-run", ...])` exits 0 and the plan ends with back_cover; templates.group_of("back_cover") == "global"; and the GUI "Whole agenda" settings widget for back_cover has a non-empty tooltip in English and Spanish (gui-marked test, MainWindow wait_idle() + close()).
Notes: Intentional exception to the constraint "every existing config.yaml must keep loading to the same Config": the user asked for the default to change, so a config without the key now loads with back_cover=False and gets no back cover (record this in STATE.md as a decision (text-fit-warnings/09)); tests/test_sample_files.py stays green because config.yaml only gains a comment. The bool field is the single switch: `back_cover` in `pages` stays ignored by build_plan (as cover/personal_info are), do not wire pages membership. Placement: no SECTIONS entry is needed (unlisted fields go to GLOBAL = "Whole agenda" tab, top-level yaml key `back_cover`); do not add it to export_model's booklets group. Assembler: in try_padding only `put(BackCover, {})` when on; with sep, append the inside-back blank filler only together with the back cover (no back cover -> no inside-back filler, the inner block runs to the last page, try_padding returns `inner` = len(entries) - lead); replace `inner_end = len(entries) - 2 if sep else len(entries)` with a count of the trailing outside pages (2 only when sep and back_cover, else 0) so index() and the folded multiple-of-4 assert stay right. Padding stays before the back cover when it exists; without it, padding is simply the tail. Update the build_plan docstring. Existing tests that expect BackCover last (test_padding.py, test_build_plan.py, test_plan_cases.py, test_summary.py comments, test_cli.py if it checks the plan tail) either pass back_cover=True or assert the new tail; tests that only list "back_cover" in pages (test_configfile.py, test_cli.py line ~49) need no change. Run the full suite: page-count expectations elsewhere may shift by 1-2 pages.
Review: PASS

## Phase 10 — Top margin for the Daily Schedule / Priorities / Notes titles   [status: done]
Deliverable: Daily._label draws the "Schedule", "Priorities" and "Notes" titles with a top margin of `tokens.SPACING[1]` (2 mm, via a named class constant such as `LABEL_TOP_GAP = tokens.SPACING[1]`, no bare numbers): the label cell starts at g.row(row) + gap and its height is g.baseline - gap, so the text stays inside its own baseline row. The title no longer touches the header band (Schedule, Priorities) or the last Priorities write-in line (Notes). Hour labels, write-in lines, column split and hour count are unchanged.
Files: agenda/pages/core.py, tests/test_daily.py
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and a test in tests/test_daily.py renders a Daily page (spying AgendaPDF.cell to record pdf.get_y() and the cell height h for each call) on A5 and on the smallest supported page size in es and en and asserts, for each of the three title texts (Strings "schedule", "priorities", "notes.title"): y >= g.header.y + g.header.h + tokens.SPACING[1] - 1e-6 for Schedule/Priorities, y >= g.row(g.rows // 2) + tokens.SPACING[1] - 1e-6 for Notes, and y + h <= g.row(r0 + 1) + 1e-6 (the title stays in its row, so it cannot reach the first hour label at g.row(1) or the first write-in line at g.row(r0 + 2)); and the number of hour-label cells ("HH:00") and the number of drawn lines equal those of the same config before the change (assert against the formula min(daily_hour_end - daily_hour_start + 1, g.rows - 1) hours).
Notes: The cause: _label (core.py ~525) puts the cell at g.row(row) with a full-baseline height, and row 0 is content.y, which is the header band's bottom edge (a filled holiday band with title_padding touches it), and row g.rows // 2 is the y of the last Priorities line. Shrinking the cell inside its row keeps the baseline grid and cannot overflow the page or push other elements. Only Daily is in scope; Monthly's "priorities" label already has a gap row and the Weekly notes label lives in a day block. Get the Grid in the test the same way the page does (grids from the renderer/render helper used by existing tests in tests/test_daily.py).
Review: FAIL -> fixed -> PASS
