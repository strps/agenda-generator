# PLAN: GUI tooltips and section-bar color legend

Goal: Every toolbar action in the GUI has a tooltip with a detailed explanation, and the section bar shows a color legend explaining what each section color means. Every config parameter widget in the settings panel gets the same two-stage tooltip as the section bar: a short text on hover, expanding after HOVER_EXPAND_MS to a detailed explanation.
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: pytest
Constraints: no new dependencies; keep existing GUI models and public API stable
Commit per phase: yes
Out of scope: changes to PDF rendering/imposition; restyling unrelated widgets

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

## Open questions

None open.

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
