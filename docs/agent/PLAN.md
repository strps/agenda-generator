# PLAN: GUI tooltips and section-bar color legend

Goal: Every toolbar action in the GUI has a tooltip with a detailed explanation, and the section bar shows a color legend explaining what each section color means. Every config parameter widget in the settings panel gets the same two-stage tooltip as the section bar: a short text on hover, expanding after HOVER_EXPAND_MS to a detailed explanation.
Goal (Phases 10-17): Split the config into global settings and per-template settings (day, week,
month, notes, qr pages), keeping config.yaml backward compatible. Day pages gain optional extras:
a rotating inspirational phrase, holiday names (library + user list) and a generic per-date
extra-data line. The GUI gets one settings tab per template plus a Global tab, a separate preview
for each template, and a coherent stylesheet/theme.
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: pytest
Constraints: no new dependencies (`holidays` is already one); keep existing GUI models and public
API stable; every existing config.yaml (flat keys) must keep loading to the same Config; Qt-free
logic lives in Qt-free modules and is tested without PySide6
Commit per phase: yes
Out of scope: imposition changes; renaming existing Config fields; restyling the PDF output.
(Phases 01-09 also excluded PDF rendering changes; Phases 10-17 change only the Daily page drawing
and the holiday lookup, and add GUI styling.)

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

## Context found while planning

- "Toolbar actions" means the plain QPushButton/QComboBox widgets (there are no QActions):
  main toolbar in agenda/gui/app.py (`open_button`, `save_button`, `export_button`) and
  the preview navigation bar in agenda/gui/preview.py (`prev_button`, `next_button`,
  `mode_buttons["single"|"spread"|"sheet"]`, `zoom_box`). gui.md mentions a "debug grid"
  checkbox, but it does not exist in code. Do not add it.
- A legend already exists. `agenda/gui/legend.py` (`Legend` widget: swatch plus flat button
  per section, click jumps to the first page) and `agenda/gui/legend_model.py`
  (`legend_entries`) are wired in app.py below the section bar. REUSE them. Do not create a
  second legend widget. What is missing is the *meaning* of each color: the buttons only say
  "Go to the first X page".
- Section keys and labels: `bar_model.SECTION_LABELS` (front_back, monthly, weekly, daily,
  optional, value_added, padding). Colors: `section_colors.PALETTE`. The meanings are in
  docs/architecture/gui.md section 3 ("Sections and colors" table).
- GUI tests use `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` plus a module-scoped
  `qapp` fixture (see tests/test_gui_shell.py and tests/test_gui_settings.py). New Qt tests must
  follow the same pattern and `pytest.importorskip("PySide6")`.

## Phase 01 — Qt-free tooltip and section-description texts   [status: done]
Deliverable: New module `agenda/gui/help_text.py` (no Qt imports) with
`TOOLTIPS: dict[str, str]` keyed by stable ids `open_config`, `save_config`, `export_pdf`,
`prev`, `next`, `mode_single`, `mode_spread`, `mode_sheet`, `zoom`, plus
`EXPORT_DISABLED_REASON: str`. It also defines `SECTION_DESCRIPTIONS: dict[str, str]` with one
entry for every key in `bar_model.SECTION_LABELS`, and `section_tooltip(key: str) -> str` that
returns "<Label>: <description>". Unknown keys fall back to the key itself.
Files: agenda/gui/help_text.py, tests/test_gui_help_text.py
Depends on: none
Done when: `pytest tests/test_gui_help_text.py` passes. The tests assert that (a) every TOOLTIPS
id above exists and each text is at least 40 chars and contains at least one sentence-ending
period; (b) `set(SECTION_DESCRIPTIONS) == set(bar_model.SECTION_LABELS)`; (c) the
`section_tooltip("padding")` text mentions "filler" or "blank"; (d)
`"agenda.gui.help_text"` imports with no PySide6 import (check via
`sys.modules` in a subprocess or by asserting the module source contains no "PySide6"). Full
`pytest` still passes.
Notes: Texts must be detailed and must explain *what happens*. Examples: Open loads a YAML config
into the settings panel and replaces current values. Save writes the current settings as YAML.
Export renders the full PDF in the background and shows progress. Single/Spread/Sheet are as in
gui.md 1. Say that Sheet is the imposed printer sheet and only applies to folded booklets. Prev/next step
by the current mode's unit. Zoom: "fit" or a fixed percentage. Section descriptions follow
gui.md section 3. Padding = auto-inserted blank filler pages, shown hatched. Use plain text, not
HTML, because the tests compare substrings.
Review: PASS

## Phase 02 — Tooltips on the main toolbar   [status: done]
Deliverable: `open_button`, `save_button` and `export_button` in agenda/gui/app.py get their
tooltips from `help_text.TOOLTIPS`. `_sync_export_button` keeps the detailed export tooltip
when valid. When invalid, it shows the detailed text plus `EXPORT_DISABLED_REASON`, and the
tooltip is never empty.
Files: agenda/gui/app.py, tests/test_gui_tooltips.py
Depends on: 01
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_tooltips.py tests/test_gui_export.py tests/test_gui_shell.py`
passes. The new tests build `MainWindow()` and assert that `open_button.toolTip()`,
`save_button.toolTip()` and `export_button.toolTip()` equal the matching TOOLTIPS texts. A further test
makes the config invalid, the same way tests/test_gui_export.py `test_export_disabled_when_config_invalid`
does, then asserts that the export tooltip contains both TOOLTIPS["export_pdf"] and
EXPORT_DISABLED_REASON. Full `pytest` passes.
Notes: Check that existing tests don't assert `export_button.toolTip() == ""`. Grep
tests/test_gui_export.py and update the assertion only if it encodes the old empty-string
behavior.
Review: PASS

## Phase 03 — Tooltips on the preview navigation bar   [status: done]
Deliverable: `prev_button`, `next_button`, each `mode_buttons[m]` and `zoom_box` in
agenda/gui/preview.py get tooltips from `help_text.TOOLTIPS` (`mode_<m>` for each m in
`preview_model.MODES`).
Files: agenda/gui/preview.py, tests/test_gui_tooltips.py
Depends on: 01
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_tooltips.py tests/test_gui_preview.py`
passes. A new test builds `PreviewWidget()` and asserts that every widget listed has a tooltip
equal to its TOOLTIPS entry. A further test asserts that every interactive child widget
(QPushButton, QComboBox) of the preview nav bar and of the main toolbar region has a non-empty
`toolTip()`. Full `pytest` passes.
Notes: If `MODES` contains a mode with no `mode_<m>` id, the test must fail (no silent skip).
Review: PASS

## Phase 04 — Color meanings in the existing legend   [status: done]
Deliverable: The existing `Legend` widget (agenda/gui/legend.py) explains each color. Each
swatch QLabel and each section button gets a tooltip of `help_text.section_tooltip(key)`
followed by a newline and "Click to go to the first <Label> page.". A leading "Legend:" QLabel
(objectName `legend_title`) gets a tooltip saying that colors mark the agenda sections in the bar
above and that hatching marks padding. `LegendEntry`, `legend_entries` and the
`section_clicked` signal stay unchanged.
Files: agenda/gui/legend.py, tests/test_gui_legend.py
Depends on: 01
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_legend.py tests/test_gui_colors.py`
passes. A new test calls `Legend().set_entries(legend_entries(build_plan(Config())))`. For every
entry it asserts that `buttons[key].toolTip()` and the `swatch_<key>` label tooltip both contain
`SECTION_DESCRIPTIONS[key]` and the text "first". It also asserts that `findChild(QLabel, "legend_title")` exists with
a non-empty tooltip. A test with a padding entry checks that the padding description is present. The
existing click test still passes. Full `pytest` passes.
Notes: Do NOT create a new legend widget or duplicate the palette. Reuse `section_colors` and
`SECTION_LABELS`. `set_entries` rebuilds the row, so the title label must be re-added there
(or kept outside the rebuilt part) and must not be deleted on each rebuild. Make sure
`recolor()` still finds the swatches by objectName.
Review: PASS

## Phase 05 — Padding swatch hatch and docs   [status: done]
Deliverable: The padding swatch in the legend shows the same 45-degree hatch as the bar
(paint a QPixmap with `Qt.BrushStyle.BDiagPattern` over gray, or use a small custom swatch
widget inside legend.py). docs/architecture/gui.md documents the toolbar tooltips and the legend
color meanings (sections 1 and 3), and drops the non-existent "debug grid" from the layout
sketch or marks it as not implemented.
Files: agenda/gui/legend.py, tests/test_gui_legend.py, docs/architecture/gui.md
Depends on: 04
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_legend.py` passes with a new test
that renders the padding swatch with `widget.grab().toImage()` and asserts it contains at least
two distinct pixel colors, while a non-padding swatch (for example monthly) contains exactly one.
`grep -n "tooltip" docs/architecture/gui.md` shows an entry in section 1 (toolbar). Full `pytest`
passes.
Notes: Keep the swatch objectName `swatch_<key>` so `recolor()` and the Phase 04 tests keep
working. The hatch must re-apply on PaletteChange.
Review: PASS

## Phase 06 — Section bar tooltip expands after a hover delay   [status: done]
Deliverable: `SectionBar` (agenda/gui/section_bar.py) first shows the existing short tooltip
(`bar_model.tooltip_text`, e.g. "Page 143 · Weekly · ..."). If the pointer stays over the same
section for `HOVER_EXPAND_MS` (a module constant, 1500), the tooltip expands to the short text,
then a newline, then `help_text.section_tooltip(key)`. The key is the section of the hovered page,
or `bar_model.PADDING` for padding pages. A single-shot `QTimer` attribute `self.expand_timer`
(interval `HOVER_EXPAND_MS`) drives the change. The hover logic moves out of `mouseMoveEvent` into
a method `hover_at(x: float, global_pos: QPoint | None = None) -> str` that updates the state and
returns the text to show. `current_tooltip() -> str` returns what is shown now. `leaveEvent`, a
left-button press/drag and `set_plan` all reset the state: the timer stops, the expansion is
cleared and the tooltip hides. `tooltip_for(x)` keeps returning the short text.
Files: agenda/gui/section_bar.py, tests/test_gui_bar.py (or new tests/test_gui_bar_hover.py), docs/architecture/gui.md
Depends on: 01
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_bar.py tests/test_gui_bar_hover.py`
(whichever holds the tests) passes. The tests use `qapp` + `importorskip("PySide6")` and a widget
from `build_plan(Config())` that has been resized to a fixed width. They drive the timer
deterministically by calling `bar.expand_timer.timeout.emit()` (or the slot it is connected to),
never `qWait` on real time. They assert:
(a) `HOVER_EXPAND_MS` is an int in 1000-3000 and equals `bar.expand_timer.interval()`, and
`expand_timer.isSingleShot()`;
(b) `hover_at(x)` returns exactly `bar_model.tooltip_text(plan, page_at(x))` and has no newline,
and the timer is then active;
(c) after the timeout fires, `current_tooltip()` equals the short text + "\n" +
`section_tooltip(key)`;
(d) `hover_at` on another page in the SAME section keeps the expanded form, with the short part
updated to the new page;
(e) `hover_at` on a page of a DIFFERENT section returns the short text only and restarts the
timer;
(f) after `bar.leaveEvent(QEvent(QEvent.Type.Leave))`, `current_tooltip() == ""` and the timer is
inactive, and the next `hover_at` returns short text;
(g) a padding page expands with the padding description.
The existing `test_widget_click_drag_keys_and_legend` and `test_tooltip_text` still pass.
`grep -n "HOVER_EXPAND_MS\|expand" docs/architecture/gui.md` finds the documented behavior in the
section bar hover bullet. Full `pytest` passes.
Notes: Keep the short format exactly as it is now. Do not change `bar_model.tooltip_text`, its
tests or `tooltip_for`. "Same section" compares section keys, not pages. Moving inside a section
must not restart the timer. Moving to another section must. Show the text with
`QToolTip.showText(global_pos, text, self)` only when `global_pos` is given; tests pass None, so
no real tooltip popup is needed offscreen. The timeout slot re-shows the expanded text at the last
global position, if one is known. Empty space or no plan: hide the tooltip and stop the timer.
Import `help_text` from the Qt-free module; do not duplicate the descriptions. In gui.md, update
the "Hover" bullet (around line 112) to describe the delayed expansion and the constant.
Review: PASS

## Context found while planning (Phases 07-09: settings parameter tooltips)

- New request: "use the same behavior for tooltips for all parameters in the config". Every config
  parameter widget in the settings panel gets a short tooltip on hover. If the pointer stays on the
  SAME widget for `HOVER_EXPAND_MS`, the tooltip expands to the short text, a newline, and a detailed
  explanation. Leaving the widget resets it. This matches Phase 06.
- Settings widgets: agenda/gui/settings_panel.py builds one editor per `settings_model.field_specs()`
  entry, one per `Config.model_fields` item in declaration order, and stores them in
  `SettingsPanel.editors[name]`. Kinds: QCheckBox (bool), QComboBox (choice/opt_choice), QSpinBox
  (int), QDoubleSpinBox (float), QGroupBox of QCheckBoxes (multi_choice: `planners`), QPlainTextEdit
  (`qr_urls`), the `pages` QGroupBox (added to the column, not the form, and it has no row label),
  and a QLineEdit for everything else. Row labels come from `form.addRow(name.replace("_", " "), w)`,
  so they are plain strings and no QLabel is kept. NO settings widget has a tooltip today.
- Config fields (agenda/config.py), 28 in total: page_size, orientation, inner_margin, outer_margin,
  bleed, booklet_size, booklet_unit, booklet_folded, num_booklets, pad_with, separate_covers,
  creep_mm, planners, daily_months, pages, preset, notes_pattern, page_numbers, qr_urls, year,
  week_start, language, holiday_country, theme, imposition, crop_marks, output, debug_grid. The tests
  must derive the list from `Config.model_fields` and must not hard-code it.
- Where meanings are documented: the comments and validators in agenda/config.py (rules such as
  imposition requiring booklet_folded, crop_marks requiring imposition, bleed needing crop_marks,
  explicit pages overriding preset, booklet_unit=pages needing a multiple of 4 (folded) or 2 (flat),
  and the qr_urls limits QR_MAX_COUNT/QR_MAX_CHARS); the parameter table in
  docs/plan/plan_script_agenda.md section 2 (lines ~24-45); the argparse `help=` strings in
  agenda/cli.py (31 of them); README.md; docs/plan/improvements.md (creep_mm). `theme` is a free string
  with no validation.
- Phase 06 mechanism: `section_bar.HOVER_EXPAND_MS = 1500`, `SectionBar.expand_timer`
  (single-shot QTimer), and `hover_at` / `_expand` / `reset_hover`. Its state is per *section key*
  inside one widget, so it cannot simply reuse a per-widget filter. Share the constant and the
  timer construction, and keep its state machine. tests/test_gui_bar_hover.py reads
  `section_bar.HOVER_EXPAND_MS`, so that name must stay importable.

## Phase 07 — Qt-free short and detailed texts for every config parameter   [status: done]
Deliverable: agenda/gui/help_text.py (still Qt-free) gains `PARAM_SHORT: dict[str, str]` and
`PARAM_DETAILS: dict[str, str]`, with one entry per `Config` field, and
`param_tooltip(name: str, expanded: bool = False) -> str`. That function returns `PARAM_SHORT[name]`,
or `PARAM_SHORT[name] + "\n" + PARAM_DETAILS[name]` when expanded. Unknown names return the name itself.
Files: agenda/gui/help_text.py, tests/test_gui_param_help.py
Depends on: none
Done when: `pytest tests/test_gui_param_help.py tests/test_gui_help_text.py` passes. The new tests
assert that:
(a) `set(PARAM_SHORT) == set(PARAM_DETAILS) == set(Config.model_fields)`;
(b) every short text is non-empty, at most 90 chars, and has no newline;
(c) every detail is at least 60 chars, ends with ".", and differs from its short text;
(d) for every spec in `settings_model.field_specs()` of kind CHOICE, OPT_CHOICE or MULTI_CHOICE, the
detail contains every value in `spec.choices`;
(e) the rule mentions: `"imposition"` in PARAM_DETAILS["crop_marks"], `"booklet_folded"` in
PARAM_DETAILS["imposition"], `"crop_marks"` in PARAM_DETAILS["bleed"], `"pages"` in
PARAM_DETAILS["preset"], `"auto"` in PARAM_DETAILS["num_booklets"], and `"mm"` in the short text of
inner_margin, outer_margin, bleed and creep_mm;
(f) `param_tooltip(n) == PARAM_SHORT[n]` and
`param_tooltip(n, True) == PARAM_SHORT[n] + "\n" + PARAM_DETAILS[n]` for every n, and
`param_tooltip("nope") == "nope"`.
The existing no-PySide6 check in tests/test_gui_help_text.py still passes. Full `pytest` passes.
Notes: Use plain text, not HTML. Take the meanings from config.py comments and validators,
plan_script_agenda.md section 2, and the cli.py help strings. Do not invent behavior. Details must say
*what changes in the output* and name the cross-field rules. help_text must not import Config or
pydantic (that keeps it light); only the test imports Config. Short texts are one phrase, for example
"Margin on the binding side, in mm.".
Review: PASS

## Phase 08 — Reusable delayed-expand tooltip, shared with SectionBar   [status: done]
Deliverable: New module agenda/gui/hover_tooltip.py, which becomes the single home of
`HOVER_EXPAND_MS = 1500` (moved from section_bar.py). section_bar.py imports it with
`from agenda.gui.hover_tooltip import HOVER_EXPAND_MS`, so `section_bar.HOVER_EXPAND_MS` still works.
The module provides `make_expand_timer(parent: QObject, slot) -> QTimer` (single-shot, interval
HOVER_EXPAND_MS, timeout connected to slot), and SectionBar uses it for `self.expand_timer`. It also
provides `class ExpandingToolTip(QObject)`, an event filter attached to one widget:
`ExpandingToolTip(widget, short: str, detail: str)` is parented to the widget, installs itself as an
event filter on it (and on `widget.viewport()` if the widget is a QAbstractScrollArea), and calls
`widget.setToolTip(short)`. Public members: `expand_timer` (from make_expand_timer), `expanded: bool`,
`hover(global_pos: QPoint | None = None) -> str`, `current_text() -> str`, `reset()`, and
`set_texts(short, detail)`. That last one updates the texts, the widget toolTip, and resets.
Behavior (same timing as SectionBar, where the timer starts as soon as the pointer is over a
section): `QEvent.Enter` on the widget (or on the scroll-area viewport) starts the expand timer, so
the expanded text is available `HOVER_EXPAND_MS` after the pointer enters. An Enter while already
expanded or with the timer running changes nothing. The filter returns False for Enter, so it is not
consumed. A `QEvent.ToolTip` on the widget (including one that propagates up from a child) calls
`hover(event.globalPos())`. That shows the current text (short, or short + "\n" + detail once
expanded) with `QToolTip.showText` when a position is given. As a fallback, if the timer is not
running and the tooltip is not expanded (for example no Enter was seen), it starts the timer. The
filter returns True. The timer timeout sets expanded and re-shows at the last ToolTip position, if
one is known. So if the native short tooltip is already up, it grows in place; otherwise the next
ToolTip event shows the expanded text directly. `QEvent.Leave` and `QEvent.Hide` on the
widget call `reset()`: the timer stops, expanded becomes False, the current text becomes "", and the
tooltip hides. These two events are not consumed (the filter returns False).
Files: agenda/gui/hover_tooltip.py, agenda/gui/section_bar.py, tests/test_gui_hover_tooltip.py
Depends on: none (Phase 06 is done)
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_hover_tooltip.py tests/test_gui_bar_hover.py tests/test_gui_bar.py`
passes, and tests/test_gui_bar_hover.py is NOT modified (`git diff --quiet -- tests/test_gui_bar_hover.py`
exits 0). `grep -rn "HOVER_EXPAND_MS *=" agenda/` prints exactly one line, in
agenda/gui/hover_tooltip.py. The new tests use the `qapp` fixture plus `importorskip("PySide6")` and
drive the timer only via `tip.expand_timer.timeout.emit()`, never by waiting in real time. They
deliver events with `QApplication.sendEvent(w, QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1)))`,
`QApplication.sendEvent(target, QHelpEvent(QEvent.Type.ToolTip, QPoint(1, 1), QPoint(1, 1)))` and
`QApplication.sendEvent(widget, QEvent(QEvent.Type.Leave))`. They assert that:
(a) `section_bar.HOVER_EXPAND_MS is hover_tooltip.HOVER_EXPAND_MS`, the timer interval equals it,
and the timer is single-shot;
(b) on a QPushButton, `toolTip() == short`; right after an Enter event (no ToolTip event yet) the
timer is active and `expanded` is False; a following ToolTip event gives `current_text() == short`;
(c) after a timeout, `expanded` is True, `current_text() == short + "\n" + detail`, and a ToolTip
event sent only after the timeout returns the expanded text (Enter, then timeout, then the first
ToolTip event shows the expanded text);
(d) another ToolTip event keeps the expanded text and leaves the timer inactive, and a second Enter
while expanded does not restart the timer;
(e) after Leave, `current_text() == ""`, the timer is inactive, `expanded` is False, and the next
Enter followed by a ToolTip event gives the short text again;
(f) a ToolTip event with no preceding Enter still starts the timer (fallback);
(g) an Enter and a ToolTip event sent to a QSpinBox's `lineEdit()` drive the ExpandingToolTip
attached to the spin box. The ToolTip event propagates; for Enter, also send the event to the spin
box itself, as Qt does when the pointer enters a child from outside;
(h) Enter and ToolTip events sent to a QPlainTextEdit's `viewport()` drive the tooltip attached to the
QPlainTextEdit;
(i) `set_texts` replaces both texts and resets.
Full `pytest` passes.
Notes: Do not change SectionBar's per-section state machine or its public methods (`hover_at`,
`current_tooltip`, `reset_hover`, `tooltip_for`). Only the constant and the timer construction are
shared. QApplication::notify propagates ToolTip events from a child with an empty tooltip to its
parents, and event filters on the parent run. That is why filters go only on the top widget, plus the
viewport for scroll areas, whose viewport events bypass the scroll area's filters. Do NOT filter
every descendant: Leave fires when moving between children and would reset too early. When the
pointer enters a child from outside, Qt delivers Enter to the parent chain as well, so the top
widget sees Enter. Repeated Enter or ToolTip events within the same widget must not restart a
running timer. Keep the module free of
settings-specific code.
Review: PASS

## Phase 09 — Expanding tooltips on every settings parameter, plus docs   [status: done]
Deliverable: SettingsPanel attaches `ExpandingToolTip(w, help_text.PARAM_SHORT[name], help_text.PARAM_DETAILS[name])`
to every editor and keeps them in a new attribute `self.tooltips: dict[str, ExpandingToolTip]`. Each
non-`pages` form row uses an explicit `QLabel` (same text as now: `name.replace("_", " ")`, objectName
`label_<name>`) with its own ExpandingToolTip and the same texts. These are stored in
`self.label_tooltips: dict[str, ExpandingToolTip]`. The `pages` group box gets the tooltip on the box
itself. `editors`, `page_boxes`, `changed`, `values()`, `set_values()` and `config()` are unchanged.
docs/architecture/gui.md documents it.
Files: agenda/gui/settings_panel.py, tests/test_gui_settings_tooltips.py, docs/architecture/gui.md
Depends on: 07, 08
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_settings_tooltips.py tests/test_gui_settings.py tests/test_gui_tooltips.py tests/test_gui_shell.py`
passes. The new tests build `SettingsPanel()` (and once `MainWindow()`, checking
`win.settings.tooltips`) and assert that:
(a) `set(panel.tooltips) == set(panel.editors) == set(Config.model_fields)`;
(b) for every name, `panel.editors[name].toolTip() == PARAM_SHORT[name]` and
`panel.tooltips[name].expand_timer.interval() == HOVER_EXPAND_MS`;
(c) for every name, sending an Enter event (QEnterEvent) to the editor (to `viewport()` for
QPlainTextEdit) makes the timer active; a following ToolTip QHelpEvent makes
`current_text() == param_tooltip(name)`; after `expand_timer.timeout.emit()` it equals
`param_tooltip(name, True)`; after a Leave event it is "" and the timer is inactive;
(d) for every name except `pages`, `panel.findChild(QLabel, f"label_{name}")` exists, its text equals
`name.replace("_", " ")`, and `panel.label_tooltips[name]` expands to `param_tooltip(name, True)`.
No timer is awaited in real time. `grep -n "PARAM_DETAILS\|hover_tooltip" docs/architecture/gui.md`
finds a match in the "Settings panel" bullet of section 1, and
`grep -n "HOVER_EXPAND_MS" docs/architecture/gui.md` still finds the section bar hover bullet. Full
`pytest` passes.
Notes: Attach the tooltips in `__init__` after `_make`, not inside `_make`, so `_make` keeps its
signature. Editing values must not touch tooltips. In gui.md, extend the Settings panel bullet:
short tooltip on hover, then after HOVER_EXPAND_MS on the same widget it expands with the detailed
explanation, texts in help_text.PARAM_SHORT/PARAM_DETAILS, mechanism in hover_tooltip.py. Update the
section bar Hover bullet so it says the constant now lives in hover_tooltip.py.
Review: PASS

## Context found while planning (Phases 10-17: per-template configs, day extras, previews, styling)

- `Config` (agenda/config.py) is one flat pydantic model with `extra="forbid"`, and every page reads
  `config.<field>` directly. Do NOT nest it or rename fields. The "global vs per-template" split is a
  *grouping* layer on top of the flat model: a Qt-free registry (new `agenda/templates.py`) assigns
  each field to `"global"` or to one template. Optional nested YAML blocks (`daily:`, `weekly:`,
  `monthly:`, `notes:`, `qr:`) are flattened to the flat field names in agenda/configfile.py, which
  already does this for `booklet:` (`BOOKLET_KEYS`, `flatten`). Flat keys keep working, so every
  existing config.yaml loads unchanged. Setting both the flat key and the block key is an error, the
  same as `booklet.size` + `booklet_size`. `daily`/`weekly` appear as *values* in `planners:`/`pages:`,
  never as top-level keys, so the new block names do not collide.
- Field use per template (from grep): `daily_months` is used by the assembler for daily pages only;
  `notes_pattern` only by `Notes` (core.py); `qr_urls` only by the `qr` page (value_added.py).
  `week_start`, `year`, `language` and `holiday_country` are used by many pages, so they stay global.
  `weekly` and `monthly` have no own fields today; their tabs are preview-only until fields exist.
- Templates and page ids: daily -> `Daily` (id `daily`, 1 page), weekly -> `Weekly` (id `weekly`,
  2 pages, `starts_on="left"`), monthly -> `Monthly` (id `monthly`), notes -> `Notes` (id `notes`),
  qr -> id `qr` (value_added.py).
- Holidays: `agenda/calendar.py: holidays_for(year, country, language)` uses the `holidays` library
  (already a dependency). `agenda/draw.py: holiday_name_for(config)` / `day_style_for(config)` wrap it
  (lru-cached `_holidays`). Weekly already prints holiday names; Daily only tints its header and does
  NOT print the name today. Monthly quotes already exist: i18n keys `quotes.1`..`quotes.12` in both
  languages (agenda/i18n.py) are used by the `quotes` page (value_added.py). Reuse them as the
  built-in daily phrase list.
- Daily page (core.py `Daily.draw`): the header band (`g.header`, 12 mm) holds the title on the left and
  the week number on the right. The footer band (`g.footer`, 6 mm, tokens.FOOTER_HEIGHT) is empty:
  `page_numbers` exists in Config but nothing draws it. Fonts "", "B", "I", "BI" are registered.
  tests/helpers.py has `render_page(cls, cfg)` and `assert_in_safe_area`; the footer is inside the
  safe area.
- Tests that pin config fields: tests/test_gui_settings.py (`field_specs()` == `Config.model_fields`,
  YAML round trip with top-level `year`), tests/test_cli.py:96 (every field except `qr_urls` needs a
  CLI option in agenda/cli.py), tests/test_gui_param_help.py (PARAM_SHORT/PARAM_DETAILS cover every
  field, and choice fields list their choices), tests/test_gui_settings_tooltips.py (tooltip per
  field). So every new Config field must also get a CLI option and help texts in the same phase.
- Settings widgets: `settings_model._kind` maps `Path | None` to TEXT, and `SettingsPanel._set` would
  write the string "None" into the QLineEdit. Optional path fields need a new kind (`OPT_PATH`) where
  "" maps to None and back.
- Preview: `PreviewWidget.set_plan(cfg, plan)` renders through `RenderJob` -> `exporter.render_pages`
  and caches by (`config_hash(cfg)`, plan index, zoom) in its own `LruCache`. `PagePlan` requires
  `entries[i].page_number == i + 1` and side == `side_for_page(i+1)`, so a per-template preview needs
  its own small sample plan built with `assembler.make_entry`, not a filtered slice of the full plan.
  One PreviewWidget per template means caches do not collide. `config_hash` hashes field values only,
  so editing the *contents* of a quotes/extra file does not invalidate the cache (acceptable; note it in
  docs).
- Styling: there is no stylesheet today. The only per-widget stylesheet is the legend swatch
  (`legend.py` `recolor`, `background-color: ...` on `swatch_<key>` labels). A global stylesheet must
  not override it (no generic `QLabel { background ... }` rule). Section colors live in
  `gui/section_colors.py` (`PALETTE`, `is_dark`). PDF colors live in `agenda/tokens.py` (`COLORS`,
  e.g. `accent`). `app.main()` builds the QApplication; tests build their own `qapp`.
- MainWindow (app.py): `self.settings` (SettingsPanel), `self.preview` (PreviewWidget) in a QSplitter,
  and `regions[L.PREVIEW] is self.preview`. tests/test_gui_shell.py checks
  `set(win.regions) == set(L.REGIONS)`. Keep `win.preview` as the full-agenda preview.

## Phase 10 — Template registry and nested YAML blocks (Qt-free)   [status: pending]
Deliverable: New Qt-free module `agenda/templates.py` with `GLOBAL = "global"`, a frozen dataclass
`TemplateSpec(key: str, label: str, page_id: str, fields: dict[str, str])` (YAML short key -> Config
field name), and `TEMPLATES: tuple[TemplateSpec, ...]`, in this order: daily ("Day pages", `daily`,
{"months": "daily_months"}), weekly ("Week pages", `weekly`, {}), monthly ("Month pages", `monthly`,
{}), notes ("Notes pages", `notes`, {"pattern": "notes_pattern"}), qr ("QR page", `qr`, {"urls":
"qr_urls"}). Functions: `template(key) -> TemplateSpec` (KeyError on unknown), `group_of(field: str) ->
str` (the template key, or GLOBAL), and `fields_of(group: str, all_fields: Iterable[str]) -> list[str]`
(keeps the given order; GLOBAL = every field not owned by a template). agenda/configfile.py `flatten`
also flattens each template block (`daily: {months: "1-6"}` -> `daily_months`) with the same errors as
`booklet:`: a non-mapping block, an unknown key (message lists the valid keys), and a block key plus
its flat key both set. A new `settings_model.config_to_yaml_data(cfg)` returns the grouped form (global
fields flat, template fields under their block, empty blocks omitted), and `save_yaml` writes that.
`config_to_data` stays flat and unchanged.
Files: agenda/templates.py, agenda/configfile.py, agenda/gui/settings_model.py,
tests/test_templates.py, tests/test_configfile.py
Depends on: none
Done when: `pytest tests/test_templates.py tests/test_configfile.py tests/test_gui_settings.py`
passes. The new tests assert that:
(a) every value in every `TemplateSpec.fields` is in `Config.model_fields`, no field belongs to two
templates, and every `page_id` resolves with `catalog.get_page`;
(b) `group_of("daily_months") == "daily"`, `group_of("year") == GLOBAL`, and the union of
`fields_of(g, Config.model_fields)` over GLOBAL plus every template key equals `set(Config.model_fields)`
with no overlap;
(c) `flatten({"daily": {"months": "1-3"}, "notes": {"pattern": "grid"}})` gives
`{"daily_months": "1-3", "notes_pattern": "grid"}`, and the three error cases raise ConfigFileError;
(d) `Config(**load_yaml("config.yaml"))` (the repo sample, unchanged) still validates, and a YAML file
with flat keys and one with the same values in blocks build equal Configs;
(e) `save_yaml` then `load_values` round-trips a Config with non-default daily_months, notes_pattern
and qr_urls, and the saved YAML has a top-level `daily:` mapping and no top-level `daily_months` key.
The existing `test_yaml_roundtrip` (top-level `year`) still passes. `git diff --quiet -- config.yaml`
exits 0. Full `pytest` passes.
Notes: templates.py must not import Config or pydantic (configfile imports it, and Config's lazy
imports must not cycle); only tests import Config. Keep `BOOKLET_KEYS` and the `booklet:` behavior
exactly as now (`save_yaml` keeps booklet fields flat). The "No rules live here" docstring of
configfile.py stays true: this is key mapping only.
Review: -

## Phase 11 — Day-extra config fields and their Qt-free data layer   [status: pending]
Deliverable: New Qt-free module `agenda/day_extras.py`: `read_lines(path) -> list[str]` (UTF-8,
strips lines, skips blank lines and lines starting with "#"; raises ValueError naming the path when it
cannot be read); `parse_dated(lines, year) -> dict[date, str]` (each line is `MM-DD text` or
`YYYY-MM-DD text`, separated by whitespace, ";" or a tab; `MM-DD` repeats every year, `YYYY-MM-DD`
applies only to that year; several entries on one date are joined with " · "; a bad line raises
ValueError with its 1-based line number); `builtin_quotes(language) -> list[str]` (i18n `quotes.1`..
`quotes.12`); `quote_for(d, quotes) -> str | None` (`quotes[(d.timetuple().tm_yday - 1) %
len(quotes)]`, None for an empty list). New Config fields, appended at the end of the "Content" block
in this order: `daily_holidays: bool = False` (print the holiday name on day pages),
`daily_quotes: bool = False`, `daily_quotes_file: Path | None = None` (one phrase per line; None = the
built-in quotes), `daily_extra_file: Path | None = None` (dated lines shown on the matching day page),
plus a global `holidays_file: Path | None = None` in the "Calendar / locale" block (user holidays in the
`parse_dated` format). Config validators check that a set file exists and parses, with a lazy import of
day_extras. templates.py: the daily block gains {"holidays": "daily_holidays", "quotes": "daily_quotes",
"quotes_file": "daily_quotes_file", "extra_file": "daily_extra_file"}; `holidays_file` stays global.
cli.py gets one option per new field. help_text.py gets PARAM_SHORT/PARAM_DETAILS for each new field.
settings_model gets an `OPT_PATH` kind for `Path | None` fields, and settings_panel maps "" <-> None
for it.
Files: agenda/day_extras.py, agenda/config.py, agenda/templates.py, agenda/cli.py,
agenda/gui/help_text.py, agenda/gui/settings_model.py, agenda/gui/settings_panel.py,
tests/test_day_extras.py, tests/test_config.py
Depends on: 10
Done when: `pytest tests/test_day_extras.py tests/test_config.py tests/test_cli.py tests/test_gui_param_help.py tests/test_gui_settings.py tests/test_gui_settings_tooltips.py tests/test_templates.py`
passes. The new tests (tmp_path files) assert that:
(a) `read_lines` skips blank and "#" lines and strips whitespace;
(b) `parse_dated(["12-25 Xmas", "2027-03-01;Trip", "12-25 Family"], 2027)` maps 2027-12-25 to
"Xmas · Family" and 2027-03-01 to "Trip", and with year 2028 drops the 2027-only line; "13-01 x" and
"no date" raise ValueError mentioning the line number;
(c) `quote_for` is deterministic, Jan 1 gives `quotes[0]`, and day 13 of a 12-item list wraps to
`quotes[0]`; `builtin_quotes("en")` has 12 non-empty entries that differ from `builtin_quotes("es")`;
(d) `Config()` defaults leave daily_holidays/daily_quotes False and the three paths None, and
`Config(daily_quotes_file=<missing>)` raises a ValidationError mentioning the field;
(e) `settings_model.field_specs()` reports kind OPT_PATH for the three path fields, and a default
SettingsPanel round-trips to `Config()` (the existing test).
Full `pytest` passes, including test_cli.py:96 and the PARAM_* coverage tests.
Notes: day_extras must not import Config (the validators import it lazily). Relative paths resolve
against the current working directory, the same as `output`. Do not add a dependency for CSV/ICS
parsing. PARAM_DETAILS must describe the file formats (`MM-DD text`, `YYYY-MM-DD text`, "#" comments)
and the rotation rule (one phrase per day of the year, cycling).
Review: -

## Phase 12 — Draw the extras on Daily pages and merge user holidays   [status: pending]
Deliverable: `draw.holiday_name_for(config)` merges `holidays_file` entries over the library holidays
(a user name on the same date replaces the library name), so the user holidays also get the holiday
tint and appear on weekly pages. `Daily.draw` (core.py) draws, only when enabled:
- `daily_holidays`: the day's holiday name in the header, right-aligned before the week number as
  "<holiday> · <week label>", muted, `TYPE_SIZES_PT[1]`; if it does not fit next to the title, it is
  truncated with "…" to fit;
- `daily_quotes`: the phrase from `quote_for(date, quotes)` in the footer band (`g.footer`), left-aligned,
  italic `TYPE_SIZES_PT[0]`, muted, truncated with "…" to fit (to half the width when extra data is also
  shown); quotes come from `daily_quotes_file` or `builtin_quotes(config.language)`;
- `daily_extra_file`: that date's text in the footer band, right-aligned, regular `TYPE_SIZES_PT[0]`,
  same truncation rule.
Files are read once per config, not once per page (cache on (path, mtime) or on the config's values
with `functools.lru_cache`). With all extras off, the output is unchanged.
Files: agenda/draw.py, agenda/pages/core.py, agenda/day_extras.py, tests/test_daily_extras.py,
tests/test_holidays.py
Depends on: 11
Done when: `pytest tests/test_daily_extras.py tests/test_daily.py tests/test_holidays.py tests/test_weekly.py tests/test_day_style.py`
(whichever of these exist) passes. The new tests render single Daily instances (set up as in
tests/helpers.py `render_page`, or by drawing one ctx) and extract text with pypdf. They assert that:
(a) with defaults, the text of a Daily page for 2027-01-01 equals the text produced before this phase
(compare with daily_holidays/daily_quotes False and no files: no " · " and no quote text);
(b) `daily_holidays=True`, `holiday_country="CR"`, `language="es"`: the 2027-01-01 page contains the
library holiday name;
(c) `daily_quotes=True` with a 2-line quotes file: Jan 1 shows line 1, Jan 2 shows line 2, Jan 3 shows
line 1; with no file, Jan 1 shows `builtin_quotes(language)[0]` (or its truncated prefix);
(d) `daily_extra_file` with "01-02 Dentist": the Jan 2 page contains "Dentist" and the Jan 1 page does not;
(e) `holidays_file` with "03-15 My day": `holiday_name_for(cfg)(date(2027, 3, 15)) == "My day"` and
`day_style_for(cfg)` returns `HOLIDAY_STYLE` for that date;
(f) `assert_in_safe_area` passes for a page with all extras on and a 300-character quote and extra text
(truncation keeps text inside the safe area).
Full `pytest` passes.
Notes: Keep `Weekly._page` unchanged except that it now sees merged holiday names through
`holiday_name_for`. The `_holidays` lru_cache key must include the holidays_file path, or the merge
must happen outside the cached function. Measure text with `pdf.get_string_width` after setting the
font. Truncation helper goes in day_extras or draw (Qt-free, unit-tested).
Review: -

## Phase 13 — Qt-free sample plans for template previews   [status: pending]
Deliverable: New Qt-free module `agenda/gui/template_model.py` with
`sample_plan(cfg: Config, key: str, instance: int = 0) -> PagePlan`. It builds a small valid PagePlan
for template `key` (or GLOBAL is rejected with ValueError) holding one instance of the template's
page class (`catalog.get_page(template(key).page_id)`), chosen as follows: daily uses the first day in
`cfg.daily_months`, others use `instances(cfg)[instance]` clamped to range. Entries come from
`assembler.make_entry` with `booklet_index=1`. A leading blank filler entry is added when the class's
`starts_on` side does not match page 1's side (so the weekly spread is a real left+right pair). Also
`included(plan: PagePlan, key: str) -> bool` (any entry of the full plan uses that page class) and
`preview_mode(key) -> str` (`preview_model.SPREAD` for page classes with `pages == 2`, else
`preview_model.SINGLE`).
Files: agenda/gui/template_model.py, tests/test_gui_template_model.py
Depends on: 10 (12 for the extras check in (d))
Done when: `pytest tests/test_gui_template_model.py` passes. Tests (no PySide6) assert that, for every
key in TEMPLATES:
(a) `sample_plan(Config(qr_urls=["x"]), key)` is a PagePlan whose non-blank entries all use the
template's page class, and `exporter.render_pages(cfg, plan, range(len(plan)))` returns a PDF with
`len(plan)` pages;
(b) weekly gives exactly one 2-page instance placed on a left/right pair (`side` values "left" then
"right" for the drawn entries);
(c) `Config(daily_months=[3])` makes the daily sample date March 1;
(d) with `daily_quotes=True` and a quotes file, the daily sample PDF text contains the first matching phrase;
(e) `included(build_plan(Config(planners=["weekly"])), "daily")` is False and
`included(build_plan(Config()), "weekly")` is True;
(f) `preview_mode("weekly") == "spread"` and `preview_mode("daily") == "single"`;
(g) the module source contains no "PySide6".
Full `pytest` passes.
Notes: Do not change `PagePlan` invariants or `build_plan`. A template whose page is not in
`cfg.pages` must still preview (the sample does not depend on the selection). Check `Grid` side
conventions in agenda/grid.py (`side_for_page`) rather than assuming page 1 is right.
Review: -

## Phase 14 — Settings panel split into Global and per-template tabs   [status: pending]
Deliverable: SettingsPanel puts its form into a `QTabWidget` (`self.tabs`, objectName
`settings_tabs`). Tab 0 is "Global" (objectName `tab_global`) with every `fields_of(GLOBAL, ...)`
editor plus the `pages` group box. Then there is one tab per TEMPLATES entry, in order, titled
`spec.label`, with objectName `tab_<key>`, holding that template's editors in `Config.model_fields`
order. Each tab is its own QScrollArea + QFormLayout. A template with no fields shows a QLabel
(objectName `tab_<key>_empty`) saying that it has no own settings yet and that the preview still shows
it. New attribute `self.tab_keys: list[str]` ([GLOBAL] + template keys, by tab index) and method
`show_tab(key: str)`. `editors`, `page_boxes`, `tooltips`, `label_tooltips` (row labels keep
`label_<name>`), `changed`, `values()`, `set_values()`, `config()`, `load_file`, `save_file` and the
`error_label` below the tabs stay unchanged.
Files: agenda/gui/settings_panel.py, tests/test_gui_settings_tabs.py
Depends on: 10, 11
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_settings_tabs.py tests/test_gui_settings.py tests/test_gui_settings_tooltips.py tests/test_gui_shell.py`
passes. The new tests (qapp fixture + `importorskip("PySide6")`) assert that:
(a) `panel.tabs.count() == 1 + len(TEMPLATES)` and the tab titles are "Global" followed by the labels;
(b) for every field name, the editor's ancestor tab page (walk `parentWidget()` up to a
`panel.tabs.widget(i)`) has index `panel.tab_keys.index(group_of(name))`;
(c) `pages` is on the Global tab, and the `weekly` and `monthly` tabs contain their `_empty` label;
(d) `show_tab("daily")` makes `panel.tabs.currentIndex() == panel.tab_keys.index("daily")`;
(e) editing a daily-tab editor emits `changed` and changes `config()`.
The unchanged tests in test_gui_settings.py and test_gui_settings_tooltips.py still pass. Full `pytest` passes.
Notes: Keep `_make` and its signature. Build all tabs before `set_values(default_values())`. Tooltip
attachment stays in `__init__` after `_make` (Phase 09 note).
Review: -

## Phase 15 — Per-template previews in the main window   [status: pending]
Deliverable: The center of MainWindow becomes a `QStackedWidget` (`self.preview_stack`). Page 0 is the
existing `self.preview` (full agenda, still `regions[L.PREVIEW]`), followed by one `PreviewWidget` per
template in `self.template_previews: dict[str, PreviewWidget]`, in TEMPLATES order, each set to
`template_model.preview_mode(key)` with zoom fit. Above each template preview is a notice QLabel
(objectName `template_notice_<key>`): empty when `included(plan, key)`, otherwise a sentence saying the
template is not in the current agenda and is shown as a sample. `settings.tabs.currentChanged` switches
the stack to the same index. `update_preview` updates the global preview as now, and updates ONLY the
visible template preview with `set_plan(cfg, sample_plan(cfg, key))`. Hidden ones are marked stale and
refreshed when their tab becomes current. On an invalid config every template preview shows the same
`set_error(msg)`. `section_bar.page_requested` and `legend.section_clicked` also switch to the Global
tab so the user sees the page they clicked.
Files: agenda/gui/app.py, tests/test_gui_template_preview.py
Depends on: 13, 14
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_template_preview.py tests/test_gui_shell.py tests/test_gui_preview.py tests/test_gui_export.py tests/test_gui_settings.py`
passes. The new tests build `MainWindow()` and assert that:
(a) `win.preview_stack.count() == 1 + len(TEMPLATES)`, `win.preview_stack.widget(0) is win.preview`,
and `win.regions[L.PREVIEW] is win.preview`;
(b) `win.settings.show_tab("daily")` makes `win.preview_stack.currentWidget() is win.template_previews["daily"]`;
after `wait_idle()` that preview's `plan` has the same length as `sample_plan(cfg, "daily")` and
`busy` is False;
(c) the weekly preview's `mode == "spread"`;
(d) with `planners=["weekly"]` loaded (via `settings.set_values`), then `flush_preview()`, the
`template_notice_daily` text is non-empty and `template_notice_weekly` text is empty;
(e) while the daily tab is current, editing a field calls `set_plan` only on the global preview and the
daily preview (patch/spy `set_plan` on the other template previews: zero calls);
(f) an invalid config (as in test_gui_export.py) leaves every template preview with `plan is None`;
(g) emitting `win.section_bar.page_requested.emit(0)` switches back to the Global tab.
Full `pytest` passes.
Notes: Do not change PreviewWidget's public API. If a new hook is needed, add it without changing
existing signatures. Each PreviewWidget owns its QThreadPool; make sure `wait_idle` is used in tests
and that window teardown does not hang (a pool per widget is acceptable). Keep the splitter: settings
left, stack center.
Review: -

## Phase 16 — Application stylesheet and theme   [status: pending]
Deliverable: New Qt-free module `agenda/gui/style_model.py` with `THEMES: dict[str, dict[str, str]]`
holding a "light" and a "dark" token set. Required tokens: window, panel, text, muted, border, accent,
accent_text, input_bg, selection, error, tooltip_bg, tooltip_text. The accent is derived from
`agenda.tokens.COLORS["accent"]` (converted to hex) for light, and is a lighter variant for dark. Also
`stylesheet(dark: bool) -> str`, which builds QSS from the tokens with rules for QMainWindow/QWidget
base colors, QPushButton (normal/hover/pressed/disabled/checked), `QPushButton#export_button` (accent
fill), QLineEdit/QSpinBox/QDoubleSpinBox/QComboBox/QPlainTextEdit, QGroupBox (+ ::title), QTabWidget::pane,
QTabBar::tab (+ :selected), QScrollArea, QToolTip, QProgressBar (+ ::chunk), `QLabel#settings_error`
(error color) and `QLabel#legend_title`. Plus `contrast_ratio(hex_a, hex_b) -> float` (WCAG formula).
In app.py, `apply_style(app: QApplication) -> None` sets `app.setStyleSheet(stylesheet(dark))` with
`dark = section_colors.is_dark(app.palette().window().color().lightness())`. `main()` calls it, and
MainWindow re-applies on `QEvent.PaletteChange`. `export_button` gets objectName `export_button`. Layout
spacing/margins on the toolbar, settings and legend get consistent values (spacing 6, margins 8).
Files: agenda/gui/style_model.py, agenda/gui/app.py, tests/test_gui_style_model.py,
tests/test_gui_style.py
Depends on: 15
Done when: `pytest tests/test_gui_style_model.py` passes (no PySide6) and
`QT_QPA_PLATFORM=offscreen pytest tests/test_gui_style.py tests/test_gui_legend.py tests/test_gui_shell.py`
passes. The tests assert that:
(a) both themes have every required token, each a `#rrggbb` hex string, and the light and dark
stylesheets differ;
(b) `contrast_ratio(text, window) >= 7`, `contrast_ratio(text, panel) >= 4.5`,
`contrast_ratio(accent_text, accent) >= 4.5`, `contrast_ratio(tooltip_text, tooltip_bg) >= 4.5`, and
`contrast_ratio(error, panel) >= 4.5` in both themes;
(c) `stylesheet(False)` contains each selector listed above, and it contains no rule whose selector is
exactly `QLabel` (regex `(^|[},\s])QLabel\s*\{` does not match);
(d) after `apply_style(qapp)`, `qapp.styleSheet() == stylesheet(dark)` for the detected mode, and a
`MainWindow()` still builds; `win.export_button.objectName() == "export_button"`;
(e) with the stylesheet applied, the legend swatch test from Phase 05 still holds: a monthly swatch
grabbed with `grab().toImage()` is a single color equal to `section_color("monthly", dark)`.
The test resets `qapp.setStyleSheet("")` at teardown so other tests are not affected. Full `pytest` passes.
Notes: Use plain QSS and no new dependency (no qt-material or similar). Do not restyle the section bar
painting or the preview page images. Keep the tooltip readable: the ExpandingToolTip texts are multi-line
plain text.
Review: -

## Phase 17 — Docs and sample config for templates and day extras   [status: pending]
Deliverable: README.md "Configuration" section documents the Global vs per-template grouping, the
optional YAML blocks (`daily:`, `weekly:`, `monthly:`, `notes:`, `qr:`), backward compatibility of flat
keys, the day extras (fields, file formats, rotation rule, user holidays) and the stale-cache caveat for
edited files. The "GUI" section documents the tabs, the per-template previews and the theme.
config.yaml gets a commented-out `daily:` block example (the active content stays equivalent).
New example files `examples/daily_quotes.txt` (at least 7 original phrases, no attribution, with a
leading "#" comment) and `examples/daily_extra.txt` (a few `MM-DD text` lines and one `YYYY-MM-DD text`
line). docs/architecture/gui.md describes the tab layout, the preview stack and style_model.py.
Files: README.md, config.yaml, examples/daily_quotes.txt, examples/daily_extra.txt,
docs/architecture/gui.md, tests/test_sample_files.py
Depends on: 12, 16
Done when: `pytest tests/test_sample_files.py` passes. It asserts that `Config(**load_yaml("config.yaml"))`
equals the Config built from the flat config.yaml at HEAD~ of this phase (hard-code the expected key
values in the test: year 2027, booklet_size 5, the same pages list), that both example files parse with
`read_lines`/`parse_dated` with no error, and that a Config with `daily_quotes_file` and
`daily_extra_file` pointing at them validates. `grep -n "daily:" README.md config.yaml` finds both,
`grep -n "holidays_file\|daily_quotes_file\|daily_extra_file" README.md` finds all three, and
`grep -n "style_model\|template_previews" docs/architecture/gui.md` finds a match. Full `pytest` passes.
Notes: Phrases must be original (same rule as the `quotes` page docstring in value_added.py). Do not
change the active (uncommented) config.yaml values.
Review: -

## Open questions

Open (Phases 10-17; the plan proceeds with the stated default unless the user answers otherwise):
- Holiday names on day pages: default `daily_holidays=False` keeps today's output byte-identical.
  Should it default to True, since Weekly already prints holiday names?
- Template list: the plan gives tabs and previews to daily, weekly, monthly, notes and qr only. Should
  the optional and value-added pages (habits, health, quotes, ...) also get a preview, for example an
  "Other pages" tab with a page picker? Default: no.
- Custom holidays (`holidays_file`) are merged everywhere: tint and names on monthly, weekly and daily.
  Should they instead appear only on day pages? Default: everywhere.
- Saved YAML now uses the grouped block form (`daily:`, `notes:`, `qr:`). Should Save keep writing flat
  keys instead? Default: grouped; both forms load.

Resolved:
- Expansion delay start (Phases 08-09): the expand timer starts when the pointer ENTERS the widget,
  so the expanded text is available about 1.5 s after entering, the same as SectionBar. The
  ToolTip event only shows the current text, and starts the timer only as a fallback.
- Row labels: the parameter's name label also gets the same expanding tooltip (Phase 09).
- `pages`: the individual page checkboxes get no per-page tooltip; the `pages` group box carries
  the tooltip.
- Legend scope: keep the current behavior. The legend lists only the sections present in the
  current plan, and the color meanings live in tooltips (Phases 04-05). No further work.
- Section-bar hover: keep the short tooltip from gui.md ("Page 143 · Weekly · ..."). If the
  pointer keeps hovering the same section for a delay, it expands to also show the section
  description (`help_text.section_tooltip`). Planned as Phase 06.
