# PLAN: GUI tooltips and section-bar color legend

Goal: Every toolbar action in the GUI has a tooltip with a detailed explanation, and the section bar shows a color legend explaining what each section color means. Every config parameter widget in the settings panel gets the same two-stage tooltip as the section bar: a short text on hover, expanding after HOVER_EXPAND_MS to a detailed explanation.
Goal (Phases 10-17): Group the config into a Global section, one section per page template that
has configuration (daily, weekly, notes, qr; see context) and a "Colors & styling" section,
keeping config.yaml backward compatible (flat keys and grouped blocks both load; Save writes the
grouped form). Day pages gain extras: holiday names (on by default; the existing holiday library
merged with an optional user `holidays_file`, treated the same on every page), a rotating inspirational phrase and a generic per-date extra-data line. The settings panel
becomes a list of collapsible sections, each template section with an enable checkbox in its
header. The main preview follows the focused or expanded section, shows that template's own
preview, and grays it out when the template is disabled. The app gets a coherent stylesheet/theme.
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: pytest
Constraints: no new dependencies (`holidays` is already one); keep existing GUI models and public
API stable; every existing config.yaml (flat keys) must keep loading to the same Config; Qt-free
logic lives in Qt-free modules and is tested without PySide6
Commit per phase: yes
Out of scope: imposition changes; renaming existing Config fields; restyling the PDF output.
(Phases 01-09 also excluded PDF rendering changes. Phases 10-17 change only the Daily page drawing
and the holiday lookup (merging the optional user `holidays_file` into it), and add GUI styling.)

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
  each field to `"global"`, to `"styling"`, or to one template. Optional nested YAML blocks (`daily:`,
  `notes:`, `qr:`, `style:`) are flattened to the flat field names in agenda/configfile.py, which
  already does this for `booklet:` (`BOOKLET_KEYS`, `flatten`). Flat keys keep working, so every
  existing config.yaml loads unchanged. Setting both the flat key and the block key is an error, the
  same as `booklet.size` + `booklet_size`. `daily`/`weekly` appear as *values* in `planners:`/`pages:`,
  never as top-level keys, so the new block names do not collide.
- Which templates have configuration (checked across agenda/pages/core.py, optional.py and
  value_added.py): every page reads only global fields (`language`, `year`, `week_start`,
  `holiday_country`) except three. `Daily` uses `daily_months` (in the assembler). `Notes` uses
  `notes_pattern`. `QRCodes` (id `qr`) uses `qr_urls`. Inclusion is also configuration:
  `build_plan` (assembler.py) adds `Weekly`/`Daily` only when "weekly"/"daily" is in `planners`, and
  adds optional/value-added pages only when their id is in `config.pages` (`_extras`). It ALWAYS adds
  `Cover`, `PersonalInfo`, `Yearly`, `Monthly`, `Notes`, `Contacts` and `BackCover`. So the sections
  with configuration are:
  daily (fields + enable via `planners`), weekly (enable via `planners`; no other field), notes
  (`notes_pattern`; always included, so its enable box is shown checked and locked), and qr
  (`qr_urls`; enable via "qr" in `pages`). Monthly, cover, yearly, contacts and the other optional
  or value-added pages have no template-specific config. They get no section and are still chosen
  in the Global section's `pages` checklist. Hard-coded class constants that could become settings
  later (not planned, see Open questions): `Daily.HOUR_START/HOUR_END` (06-21),
  `Schedule.FIRST_HOUR`, `Habits.MAX_HABITS`, and the `count` constructor argument of
  `Notes`/`Contacts`/niche packs (`_Counted`), which the assembler always leaves at 1.
- "Colors & styling" section: `theme` (Config field, free string, `agenda/themes.py` is an empty stub)
  plus a GUI-only "App appearance" combo (system/light/dark) that is not a Config field. Global = every
  other field, including `planners` and `pages`; the header boxes are views of those editors.
- Templates and page ids: daily -> `Daily` (id `daily`, 1 page), weekly -> `Weekly` (id `weekly`,
  2 pages, `starts_on="left"`), notes -> `Notes` (id `notes`), qr -> `QRCodes` (id `qr`).
- `preset` pitfall: `Config._resolve_preset` fills an empty `pages` from `preset`. Enabling qr through its
  header box when `pages` is empty and a preset is set must first copy `preset_pages(preset)` into
  `pages`, otherwise the explicit list silently drops the preset's pages.
- Holidays: `agenda/calendar.py: holidays_for(year, country, language)` uses the `holidays` library
  (already a dependency). `agenda/draw.py: holiday_name_for(config)` / `day_style_for(config)` wrap it
  (lru-cached `_holidays`). Yearly/Monthly mini-months and grids, Weekly (tint + name) and Daily (tint
  only; it does NOT print the name today) use them. The `holidays` page (optional.py `Holidays.draw`)
  calls `holidays_for` directly, so Phase 12 adds `draw.merged_holidays` as the one source for all of them. The user `holidays_file` (Phase 11/12) is merged INTO this lookup, so its entries
  are ordinary holidays everywhere: same tint, same name display, and no separate styling, flag or
  code path. Monthly quotes already exist: i18n keys
  `quotes.1`..`quotes.12` in both languages (agenda/i18n.py) are used by the `quotes` page
  (value_added.py). Reuse them as the built-in daily phrase list.
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

## Phase 10 — Section registry, enable rules and nested YAML blocks (Qt-free)   [status: pending]
Deliverable: New Qt-free module `agenda/templates.py` with `GLOBAL = "global"`, `STYLING = "styling"`,
and a frozen dataclass `SectionSpec(key: str, label: str, block: str | None, fields: dict[str, str],
page_id: str | None = None, enable: str = "none")`. `fields` maps YAML short key -> Config field
name; `enable` is one of "planner", "page", "always" or "none". `SECTIONS: tuple[SectionSpec, ...]`
lists them in display order:
- global ("Global", block None, fields = every field not owned elsewhere, computed);
- daily ("Day pages", block "daily", {"months": "daily_months"}, page_id "daily", enable "planner");
- weekly ("Week pages", block None, {}, page_id "weekly", enable "planner");
- notes ("Notes pages", block "notes", {"pattern": "notes_pattern"}, page_id "notes", enable "always");
- qr ("QR codes", block "qr", {"urls": "qr_urls"}, page_id "qr", enable "page");
- styling ("Colors & styling", block "style", {"theme": "theme"}).
`TEMPLATE_KEYS` = the keys that have a page_id. Functions:
- `section(key)` (KeyError on unknown);
- `group_of(field) -> str`;
- `fields_of(key, all_fields) -> list[str]` (keeps the given order; GLOBAL gets the rest);
- `is_enabled(cfg, key) -> bool` (planner: key in cfg.planners; page: page_id in (cfg.pages or []);
  always: True);
- `with_enabled(values: dict, key, on: bool) -> dict` (returns a new raw-values dict with
  planners/pages updated. For "page" with empty pages and a set preset, it first copies
  `catalog.preset_pages(preset)`. "always" raises ValueError).
agenda/configfile.py `flatten` also flattens every section block (`daily: {months: "1-6"}` ->
`daily_months`) with the same errors as `booklet:`: a non-mapping block, an unknown key (the message
lists the valid keys), and a block key plus its flat key both set. New
`settings_model.config_to_yaml_data(cfg)` returns the grouped form: global fields flat, section fields
under their block, empty blocks omitted. `save_yaml` writes that form. `config_to_data` stays flat and
unchanged.
Files: agenda/templates.py, agenda/configfile.py, agenda/gui/settings_model.py,
tests/test_templates.py, tests/test_configfile.py
Depends on: none
Done when: `pytest tests/test_templates.py tests/test_configfile.py tests/test_gui_settings.py`
passes. The new tests assert that:
(a) every field in every `SectionSpec.fields` is in `Config.model_fields`; no field is in two sections;
every page_id resolves with `catalog.get_page`; and the `fields_of` lists over all SECTIONS partition
`Config.model_fields` exactly;
(b) `group_of("daily_months") == "daily"`, `group_of("theme") == STYLING`,
`group_of("planners") == group_of("pages") == group_of("year") == GLOBAL`;
(c) `is_enabled(Config(planners=["weekly"]), "daily")` is False and the weekly result is True;
`is_enabled(Config(), "notes")` is True; `is_enabled(Config(pages=["qr"], qr_urls=["x"]), "qr")` is True;
(d) `with_enabled(default_values(), "daily", False)["planners"] == ["weekly"]`; enabling qr on
`{**default_values(), "preset": "essential"}` gives a pages list equal to
`preset_pages("essential") + ["qr"]` (no duplicate if already present); `with_enabled(..., "notes", False)`
raises ValueError;
(e) `flatten({"daily": {"months": "1-3"}, "notes": {"pattern": "grid"}, "style": {"theme": "x"}})` gives
the three flat keys, and the three error cases raise ConfigFileError;
(f) `Config(**load_yaml("config.yaml"))` (the repo sample, unchanged) still validates, and flat-key and
block YAML files with the same values build equal Configs;
(g) `save_yaml` then `load_values` round-trips a Config with non-default daily_months, notes_pattern,
qr_urls and theme; the saved YAML has top-level `daily:` and `style:` mappings and no top-level
`daily_months` key.
The existing `test_yaml_roundtrip` (top-level `year`) still passes. `git diff --quiet -- config.yaml`
exits 0. Full `pytest` passes.
Notes: templates.py must not import Config or pydantic at module level (configfile imports it, and
Config's lazy imports must not cycle). `is_enabled`/`with_enabled` duck-type on `cfg` and use a lazy
`catalog` import. Keep `BOOKLET_KEYS` and the `booklet:` behavior exactly as now (`save_yaml` keeps the
booklet fields flat). The "No rules live here" docstring of configfile.py stays true: this is key
mapping only. Adding a future section must be a one-entry change to SECTIONS.
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
in this order: `daily_holidays: bool = True` (print the holiday name on day pages; the name comes
from the existing `holiday_name_for` lookup), `daily_quotes: bool = False`,
`daily_quotes_file: Path | None = None` (one phrase per line; None = the built-in quotes), and
`daily_extra_file: Path | None = None` (dated lines shown on the matching day page). Add a global
`holidays_file: Path | None = None` in the "Calendar / locale" block, right after `holiday_country`
(user holidays in the `parse_dated` format). Config validators check that a set file exists and
parses, with a lazy import of day_extras. In templates.py the daily section's fields gain {"holidays":
"daily_holidays", "quotes": "daily_quotes", "quotes_file": "daily_quotes_file", "extra_file":
"daily_extra_file"}. `holidays_file` stays in GLOBAL.
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
(d) `Config()` defaults are daily_holidays True, daily_quotes False and the three paths None;
`Config(daily_quotes_file=<missing>)` and `Config(holidays_file=<file with a bad line>)` raise a
ValidationError that mentions the field; `templates.group_of("holidays_file") == GLOBAL`;
(e) `settings_model.field_specs()` reports kind OPT_PATH for the three path fields, and a default
SettingsPanel round-trips to `Config()` (the existing test).
Full `pytest` passes, including test_cli.py:96 and the PARAM_* coverage tests.
Notes: day_extras must not import Config (the validators import it lazily). Relative paths resolve
against the current working directory, the same as `output`. Do not add a dependency for CSV/ICS
parsing. PARAM_DETAILS must describe the file formats (`MM-DD text`, `YYYY-MM-DD text`, "#" comments)
and the rotation rule (one phrase per day of the year, cycling).
Review: -

## Phase 12 — Merge user holidays; draw the extras on Daily pages (holiday names on by default)   [status: pending]
Deliverable: New `draw.merged_holidays(config) -> dict[date, str]`, sorted by date, becomes the
single holiday source. It returns the library holidays (`holidays_for`) plus the `holidays_file`
entries (via `day_extras.parse_dated` for `config.year`). On a date that has both, the names are
joined with " · ", library name first. With an unsupported country it returns only the user entries;
callers that today let the ValueError through keep doing so when there is no file.
`holiday_name_for` and `day_style_for` use it. The `Holidays` page (optional.py `Holidays.draw`, which
today calls `holidays_for` directly) switches to it. So every page (Yearly, Monthly, Weekly, Daily,
`holidays`) treats user holidays exactly like library holidays: there is no separate styling, flag or
code path. `Daily.draw` (core.py) uses the same lookup and draws, when enabled:
- `daily_holidays`: the day's holiday name in the header, right-aligned before the week number as
  "<holiday> · <week label>", muted, `TYPE_SIZES_PT[1]`; if it does not fit next to the title, it is
  truncated with "…" to fit;
- `daily_quotes`: the phrase from `quote_for(date, quotes)` in the footer band (`g.footer`), left-aligned,
  italic `TYPE_SIZES_PT[0]`, muted, truncated with "…" to fit (to half the width when extra data is also
  shown); quotes come from `daily_quotes_file` or `builtin_quotes(config.language)`;
- `daily_extra_file`: that date's text in the footer band, right-aligned, regular `TYPE_SIZES_PT[0]`,
  same truncation rule.
Files are read once per config, not once per page (cache on (path, mtime) or on the config's values
with `functools.lru_cache`). With `daily_holidays=False` and the other extras off, the output equals
today's output. With defaults, holiday days now also show the holiday name.
Files: agenda/draw.py, agenda/pages/core.py, agenda/pages/optional.py, agenda/day_extras.py,
tests/test_daily_extras.py, tests/test_user_holidays.py, tests/test_daily.py
Depends on: 11
Done when: `pytest tests/test_daily_extras.py tests/test_user_holidays.py tests/test_daily.py tests/test_holidays.py tests/test_weekly.py tests/test_day_style.py tests/test_monthly.py`
(whichever of these exist) passes. The new tests render single Daily instances (set up as in
tests/helpers.py `render_page`, or by drawing one ctx) and extract text with pypdf. They assert that:
(a) with `daily_holidays=False` and no other extras, the 2027-01-01 Daily page text has no " · " and
no quote text (the old output);
(b) with DEFAULTS (`holiday_country="CR"`, `language="es"`), the 2027-01-01 page contains
`holiday_name_for(cfg)(date(2027, 1, 1))`, and a non-holiday weekday (for example 2027-01-05) has no " · ";
(c) consistency: for that holiday date the name returned by `holiday_name_for` is the one printed on
both the Daily page and the Weekly spread containing it, and `day_style_for(cfg)(d) is HOLIDAY_STYLE`;
(d) `daily_quotes=True` with a 2-line quotes file: Jan 1 shows line 1, Jan 2 shows line 2, Jan 3 shows
line 1; with no file, Jan 1 shows `builtin_quotes(language)[0]` (or its truncated prefix);
(e) `daily_extra_file` with "01-02 Dentist": the Jan 2 page contains "Dentist" and the Jan 1 page does not;
(f) `assert_in_safe_area` passes for a page with all extras on, a 300-character quote and extra text,
and a holiday (truncation keeps text inside the safe area);
(g) the truncation helper returns the input unchanged when it fits and ends with "…" otherwise;
(h) user holidays (tests/test_user_holidays.py, tmp_path file with "03-15 My day" and "01-01 Family"):
`holiday_name_for(cfg)(date(2027, 3, 15)) == "My day"`; `day_style_for(cfg)(date(2027, 3, 15)) is
HOLIDAY_STYLE` (the same object as for library holidays, not a new style); Jan 1 gives
"<library name> · Family"; "My day" appears in the text of the 2027-03-15 Daily page, of the Weekly spread
containing it, and of the `holidays` page; with `holidays_file=None`, `merged_holidays(cfg) ==
holidays_for(2027, "CR", "es")`; with an unsupported country plus the file, `merged_holidays` returns only
the user entries.
Full `pytest` passes.
Notes: `Weekly._page` and the mini-month code stay unchanged: they pick up user holidays through
`holiday_name_for`/`day_style_for`. The `_holidays` lru_cache is keyed on (year, country, language). Do
the merge outside it, or add the file path (plus mtime) to the key. Existing Daily tests that pin exact
text may need a `daily_holidays=False` config; update only those assertions, and never weaken the
safe-area checks. Measure text with `pdf.get_string_width` after setting the font. The truncation helper
goes in day_extras (Qt-free, unit-tested).
Review: -

## Phase 13 — Qt-free sample plans for template previews   [status: pending]
Deliverable: New Qt-free module `agenda/gui/template_model.py` with
`sample_plan(cfg: Config, key: str, instance: int = 0) -> PagePlan`. It builds a small valid PagePlan
for template `key` (a key in `templates.TEMPLATE_KEYS`; GLOBAL, STYLING or unknown keys raise
ValueError) holding one instance of the template's
page class (`catalog.get_page(section(key).page_id)`), chosen as follows: daily uses the first day in
`cfg.daily_months`, others use `instances(cfg)[instance]` clamped to range. Entries come from
`assembler.make_entry` with `booklet_index=1`. A leading blank filler entry is added when the class's
`starts_on` side does not match page 1's side (so the weekly spread is a real left+right pair). The qr
sample uses a placeholder URL list (`["https://example.com"]`) when `cfg.qr_urls` is empty, so it never
renders an empty page. Also `preview_mode(key) -> str` (`preview_model.SPREAD` for page classes with
`pages == 2`, else `preview_model.SINGLE`), and `preview_target(active: str, last_template: str | None)
-> str`. That last one decides which preview the main window shows: a template key shows itself, GLOBAL
shows GLOBAL (the full agenda), and STYLING shows `last_template` if set, else GLOBAL.
Files: agenda/gui/template_model.py, tests/test_gui_template_model.py
Depends on: 10 (12 for the extras check in (d))
Done when: `pytest tests/test_gui_template_model.py` passes. Tests (no PySide6) assert that, for every
key in TEMPLATE_KEYS:
(a) `sample_plan(Config(), key)` is a PagePlan whose non-blank entries all use the
template's page class, and `exporter.render_pages(cfg, plan, range(len(plan)))` returns a PDF with
`len(plan)` pages;
(b) weekly gives exactly one 2-page instance placed on a left/right pair (`side` values "left" then
"right" for the drawn entries);
(c) `Config(daily_months=[3])` makes the daily sample date March 1;
(d) with `daily_quotes=True` and a quotes file, the daily sample PDF text contains the first matching phrase;
(e) `sample_plan(Config(planners=["weekly"]), "daily")` still works: a disabled template still has a sample;
(f) `preview_mode("weekly") == "spread"` and `preview_mode("daily") == "single"`;
(g) `preview_target("daily", None) == "daily"`, `preview_target(GLOBAL, "daily") == GLOBAL`,
`preview_target(STYLING, "qr") == "qr"`, `preview_target(STYLING, None) == GLOBAL`; `sample_plan(cfg,
GLOBAL)` and `sample_plan(cfg, STYLING)` raise ValueError;
(h) the module source contains no "PySide6".
Full `pytest` passes.
Notes: Do not change `PagePlan` invariants or `build_plan`. A disabled template must still preview
(the sample does not depend on `planners`/`pages`; the GUI grays it out in Phase 15). Check `Grid` side
conventions in agenda/grid.py (`side_for_page`) rather than assuming page 1 is right.
Review: -

## Phase 14 — Collapsible sections with enable checkboxes in the settings panel   [status: pending]
Deliverable: New module agenda/gui/collapsible.py with `CollapsibleSection(QFrame)`, constructed as
`CollapsibleSection(key: str, title: str, enable: str = "none")` (objectName `section_<key>`). Its
header has a `toggle_button` (checkable QToolButton showing an arrow and the title, objectName
`section_toggle`) and an `enable_box`. The box is a QCheckBox (objectName `section_enable`) when
`enable` is "planner" or "page". For "always" it is a checked, disabled QCheckBox whose tooltip says
the page is always included. For "none" it is None. Below the header is a `body` QWidget with a
QFormLayout `form`. API: `set_expanded(bool)`, `is_expanded()`, `set_enabled_state(bool)` (sets the
box with signals blocked and calls `body.setEnabled`), `enabled_state() -> bool`. Signals:
`expanded_changed(bool)` and `enable_toggled(bool)` (user toggles only). Unchecking the box disables
`body`, which grays out all its controls; the header stays usable. SettingsPanel builds one section per
`templates.SECTIONS` entry, in order, inside the existing scroll area, and places every editor in the
section `group_of(name)` (the `pages` box and `planners` go in Global). Global starts expanded and the
others collapsed. New members: `self.sections: dict[str, CollapsibleSection]`,
`self.active_section: str` (initially GLOBAL), the signal `section_activated = Signal(str)`,
`activate(key)` (expand, set active, emit), and `notify_focus(widget)`. `notify_focus` is connected to
`QApplication.focusChanged` and activates the section that contains the newly focused widget.
Expanding a section also activates it. Header boxes are views of the existing editors. A toggle
computes `templates.with_enabled(self.values(), key, on)`, writes back only the `planners` and `pages`
editors (via `_set`, with `_loading` set), and then emits `changed` once. After every change
(`changed`), each box is re-synced from `templates.is_enabled` on the current values. `editors`,
`page_boxes`, `tooltips`, `label_tooltips` (row labels keep `label_<name>`), `changed`, `values()`,
`set_values()`, `config()`, `load_file`, `save_file` and `error_label` keep their behavior.
Files: agenda/gui/collapsible.py, agenda/gui/settings_panel.py, tests/test_gui_collapsible.py,
tests/test_gui_settings_sections.py
Depends on: 10, 11
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_collapsible.py tests/test_gui_settings_sections.py tests/test_gui_settings.py tests/test_gui_settings_tooltips.py tests/test_gui_shell.py`
passes, and tests/test_gui_settings.py and tests/test_gui_settings_tooltips.py are NOT modified
(`git diff --quiet -- tests/test_gui_settings.py tests/test_gui_settings_tooltips.py` exits 0). The new
tests (qapp fixture + `importorskip("PySide6")`) assert that:
(a) CollapsibleSection: `set_expanded(True)` shows the body (`body.isVisibleTo(section)`) and emits
`expanded_changed(True)`; `enable_box.setChecked(False)` emits `enable_toggled(False)` and makes
`body.isEnabled()` False; `set_enabled_state(True)` re-enables the body without emitting `enable_toggled`;
"always" gives a checked, disabled box; "none" gives `enable_box is None`;
(b) `list(panel.sections) == [s.key for s in SECTIONS]` and each toggle_button text equals the section label;
(c) for every field name, the nearest CollapsibleSection ancestor of `panel.editors[name]` has key
`group_of(name)`;
(d) defaults: the daily and weekly boxes are checked, the notes box is checked and disabled, the qr box
is unchecked, and `panel.editors["qr_urls"].isEnabled()` is False; the global and styling sections have
no box;
(e) unchecking the daily box gives `panel.config()[0].planners == ["weekly"]`, emits `changed`, disables
`editors["daily_months"]`, and unchecks the "daily" checkbox inside `editors["planners"]`; checking that
"daily" checkbox again re-checks the header box and re-enables the body;
(f) with `preset` "essential" and no pages, checking the qr box gives
`cfg.pages == preset_pages("essential") + ["qr"]` (pass qr_urls so the config is valid), and
`page_boxes["qr"]` is checked;
(g) `panel.sections["daily"].set_expanded(True)` emits `section_activated("daily")` and sets
`active_section`; `panel.notify_focus(panel.editors["qr_urls"])` emits `section_activated("qr")`;
`notify_focus(None)` and widgets outside the panel emit nothing;
(h) `set_values(...)` with `planners: ["daily"]` re-syncs the weekly box to unchecked.
Full `pytest` passes.
Notes: Keep `_make` and its signature. Tooltip attachment stays in `__init__` after `_make` (Phase 09
note). Phase 09 tooltip tests send Enter/ToolTip events to every editor, including editors inside a
disabled body (qr is off by default). Qt delivers these events to disabled widgets, but if a test fails
there, fix the panel, not the tests. Do not make the sections an accordion: several may be open at once,
and "active" is the last one expanded or focused. Do not duplicate `planners`/`pages` state. The header
boxes always read it from the editors.
Review: -

## Phase 15 — Main preview follows the active section; disabled templates grayed out   [status: pending]
Deliverable: The center of MainWindow becomes a `QStackedWidget` (`self.preview_stack`). Page 0 is the
existing `self.preview` (full agenda, still `regions[L.PREVIEW]`). Then there is one page per key in
`TEMPLATE_KEYS`: a container (objectName `template_page_<key>`) with a notice QLabel
(`template_notice_<key>`) above a `PreviewWidget`. These are kept in
`self.template_previews: dict[str, PreviewWidget]`, each set to `template_model.preview_mode(key)` with
zoom fit. `settings.section_activated` calls `show_preview_for(key)`, which shows
`preview_target(key, self.last_template)` and updates `self.last_template` when key is a template.
Decision (user point 5): Global shows the full-agenda preview, and "Colors & styling" shows the last
active template's preview, or the full agenda if none was active yet. `self.preview_key` is the key
shown. PreviewWidget gains an additive `set_inactive(on: bool)` and an `inactive` attribute. When on, a
`QGraphicsOpacityEffect` (opacity 0.35) is applied to its scroll area. When off, the effect is removed.
A template preview is inactive when `not templates.is_enabled(cfg, key)`, and its notice then says
the template is disabled and is not included in the agenda; otherwise the notice is empty.
`update_preview` updates the full preview as now, and ONLY the visible template preview, with
`set_plan(cfg, sample_plan(cfg, key))` plus `set_inactive`. Hidden ones are marked stale and refreshed
when shown. On an invalid config every template preview gets `set_error(msg)`.
`section_bar.page_requested` and `legend.section_clicked` call `show_preview_for(GLOBAL)`, so the
clicked page is visible.
Files: agenda/gui/app.py, agenda/gui/preview.py, tests/test_gui_template_preview.py
Depends on: 13, 14
Done when: `QT_QPA_PLATFORM=offscreen pytest tests/test_gui_template_preview.py tests/test_gui_shell.py tests/test_gui_preview.py tests/test_gui_export.py tests/test_gui_settings.py`
passes. The new tests build `MainWindow()` and assert that:
(a) `win.preview_stack.count() == 1 + len(TEMPLATE_KEYS)`, `win.preview_stack.widget(0) is win.preview`,
and `win.regions[L.PREVIEW] is win.preview`; initially `win.preview_key == GLOBAL`;
(b) `win.settings.activate("daily")` makes the stack's current page `template_page_daily`; after
`wait_idle()` the daily preview's `plan` has the length of `sample_plan(cfg, "daily")` and `busy` is False;
`win.settings.notify_focus(win.settings.editors["qr_urls"])` switches to `template_page_qr`;
(c) `activate(STYLING)` after daily keeps the daily page, and on a fresh window it shows page 0;
`activate(GLOBAL)` shows page 0;
(d) the weekly preview's `mode == "spread"`;
(e) defaults: the qr preview is `inactive` with a non-empty notice and has a `QGraphicsOpacityEffect` on its
scroll area; checking the qr header box (with qr_urls set) then `flush_preview()` makes it active,
removes the effect and empties the notice; unchecking daily makes the daily preview inactive;
(f) while daily is shown, editing a field calls `set_plan` only on the full preview and the daily preview
(spy on the others: zero calls);
(g) an invalid config (as in test_gui_export.py) leaves every template preview with `plan is None`;
(h) `win.section_bar.page_requested.emit(0)` switches to page 0.
Full `pytest` passes.
Notes: Do not change existing PreviewWidget signatures. `set_inactive` is additive and must survive
`refresh()` (refresh must not drop the effect). Each PreviewWidget owns its QThreadPool; use `wait_idle`
in tests and make sure window teardown does not hang. Keep the splitter: settings on the left, stack
in the center. The section bar, legend and summary always describe the full agenda.
Review: -

## Phase 16 — Application stylesheet and theme   [status: pending]
Deliverable: New Qt-free module `agenda/gui/style_model.py` with `THEMES: dict[str, dict[str, str]]`
holding a "light" and a "dark" token set. Required tokens: window, panel, text, muted, border, accent,
accent_text, input_bg, selection, error, tooltip_bg, tooltip_text. The accent is derived from
`agenda.tokens.COLORS["accent"]` (converted to hex) for light, and is a lighter variant for dark. Also
`stylesheet(dark: bool) -> str`, which builds QSS from the tokens with rules for QMainWindow/QWidget
base colors, QPushButton (normal/hover/pressed/disabled/checked), `QPushButton#export_button` (accent
fill), QLineEdit/QSpinBox/QDoubleSpinBox/QComboBox/QPlainTextEdit (+ :disabled in the muted color),
QGroupBox (+ ::title), `QFrame[objectName^="section_"]` or an equivalent section-frame rule,
`QToolButton#section_toggle` (bold header, hover), `QCheckBox#section_enable`, QScrollArea, QToolTip,
QProgressBar (+ ::chunk), `QLabel#settings_error` (error color), `QLabel#legend_title` and the
`template_notice_*` labels. Also `contrast_ratio(hex_a, hex_b) -> float` (WCAG formula),
`APPEARANCES = ("system", "light", "dark")` and `resolve_dark(appearance, window_lightness) -> bool`
("system" uses `section_colors.is_dark`). In app.py, `apply_style(app, appearance="system")` sets
`app.setStyleSheet(stylesheet(resolve_dark(...)))`. `main()` calls it, and MainWindow re-applies on
`QEvent.PaletteChange`. The "Colors & styling" section gets a GUI-only `settings.appearance_box`
(QComboBox over APPEARANCES, objectName `appearance`, with an ExpandingToolTip from new
`help_text.TOOLTIPS["appearance"]`). It is NOT a Config field, is not in `editors`, `values()` or the YAML,
and changing it calls `apply_style` for the running app. `export_button` gets objectName
`export_button`. Layout spacing/margins on the toolbar, settings sections and legend get consistent
values (spacing 6, margins 8).
Files: agenda/gui/style_model.py, agenda/gui/app.py, agenda/gui/settings_panel.py,
agenda/gui/help_text.py, tests/test_gui_style_model.py, tests/test_gui_style.py
Depends on: 15
Done when: `pytest tests/test_gui_style_model.py tests/test_gui_help_text.py` passes (no PySide6) and
`QT_QPA_PLATFORM=offscreen pytest tests/test_gui_style.py tests/test_gui_legend.py tests/test_gui_shell.py tests/test_gui_settings.py`
passes. The tests assert that:
(a) both themes have every required token, each a `#rrggbb` hex string, and the light and dark
stylesheets differ; `resolve_dark("light", 0) is False`, `resolve_dark("dark", 255) is True`,
`resolve_dark("system", 20) is True`;
(b) `contrast_ratio(text, window) >= 7`, `contrast_ratio(text, panel) >= 4.5`,
`contrast_ratio(accent_text, accent) >= 4.5`, `contrast_ratio(tooltip_text, tooltip_bg) >= 4.5`, and
`contrast_ratio(error, panel) >= 4.5` in both themes;
(c) `stylesheet(False)` contains each selector listed above, and it contains no rule whose selector is
exactly `QLabel` (regex `(^|[},\s])QLabel\s*\{` does not match);
(d) after `apply_style(qapp)`, `qapp.styleSheet() == stylesheet(dark)` for the detected mode, and a
`MainWindow()` still builds; `win.export_button.objectName() == "export_button"`;
(e) `win.settings.appearance_box` is inside `sections[STYLING]`; selecting "dark" makes
`qapp.styleSheet() == stylesheet(True)`, and "light" makes it `stylesheet(False)`; `values()` has no
"appearance" key and `config()` is unchanged by it;
(f) with the stylesheet applied, the legend swatch test from Phase 05 still holds: a monthly swatch
grabbed with `grab().toImage()` is a single color equal to `section_color("monthly", dark)`.
The test resets `qapp.setStyleSheet("")` at teardown so other tests are not affected. Full `pytest` passes.
Notes: Use plain QSS and no new dependency (no qt-material or similar). Do not restyle the section bar
painting or the preview page images. Keep the tooltip readable: the ExpandingToolTip texts are multi-line
plain text. Disabled section bodies must look clearly grayed (`:disabled` rules) but stay legible
(`contrast_ratio(muted, panel) >= 3`, also asserted in (b)). The appearance choice is not persisted (see
Open questions).
Review: -

## Phase 17 — Docs and sample config for templates and day extras   [status: pending]
Deliverable: README.md "Configuration" section documents the grouping into Global, per-template and
Colors & styling sections, the optional YAML blocks (`daily:`, `notes:`, `qr:`, `style:`), the fact that
Save writes blocks while flat keys still load, the day extras (fields, file formats, rotation rule,
holiday names on by default) and `holidays_file` (merged into the regular holidays on every page). It
also notes the stale-cache caveat for edited files. The "GUI" section documents the collapsible
sections, the enable checkboxes (what each one maps to: planners / pages / always on), the preview that
follows the active section (Global = full agenda, Colors & styling = last template), grayed-out disabled
templates, and the appearance setting.
config.yaml gets a commented-out `daily:` block example (the active content stays equivalent).
New example files `examples/daily_quotes.txt` (at least 7 original phrases, no attribution, with a
leading "#" comment) and `examples/daily_extra.txt` (a few `MM-DD text` lines and one `YYYY-MM-DD text`
line), and `examples/holidays.txt` (a few `MM-DD name` lines). docs/architecture/gui.md describes
collapsible.py, the section layout, the preview stack and `preview_target`, and style_model.py.
Files: README.md, config.yaml, examples/daily_quotes.txt, examples/daily_extra.txt,
examples/holidays.txt, docs/architecture/gui.md, tests/test_sample_files.py
Depends on: 12, 16
Done when: `pytest tests/test_sample_files.py` passes. It asserts that `Config(**load_yaml("config.yaml"))`
equals the Config built from the flat config.yaml at HEAD~ of this phase (hard-code the expected key
values in the test: year 2027, booklet_size 5, the same pages list). It also asserts that the three
example files parse with `read_lines`/`parse_dated` with no error, and that a Config with
`daily_quotes_file`, `daily_extra_file` and `holidays_file` pointing at them validates.
`grep -n "daily:" README.md config.yaml` finds both,
`grep -n "holidays_file\|daily_quotes_file\|daily_extra_file" README.md` finds all three, and
`grep -n "collapsible\|preview_target\|style_model" docs/architecture/gui.md` finds all three. Full
`pytest` passes.
Notes: Phrases must be original (same rule as the `quotes` page docstring in value_added.py). Do not
change the active (uncommented) config.yaml values.
Review: -

## Open questions

Open (Phases 10-17; the plan proceeds with the stated default unless the user answers otherwise):
- New per-template settings: the code hard-codes values that could become sections later: daily
  schedule hours (`Daily.HOUR_START/HOUR_END`, 06-21), the schedule page's `FIRST_HOUR`,
  `Habits.MAX_HABITS`, and the page count of Notes/Contacts/niche packs (always 1). Should any of them
  become config fields, each giving its template its own section? Default: no. The SECTIONS registry
  makes each one a one-entry addition later.
- Notes and other core pages (cover, yearly, monthly, contacts, back cover) are always in the agenda.
  The notes section's enable box is shown checked and locked. Should core pages become switchable (a
  new Config field)? Default: no.
- App appearance (system/light/dark) is GUI-only and not persisted across runs. Should it be saved
  (QSettings or the YAML)? Default: not persisted.

Resolved:
- Holiday names on day pages default to ON (`daily_holidays=True`, Phases 11-12).
- Sections, not tabs: one collapsible section per template that has configuration (daily, weekly,
  notes, qr, from a code audit), each with an enable checkbox in its header. Unchecked = controls
  disabled and the preview grayed out. The main preview follows the focused or expanded section
  (Phases 14-15).
- `holidays_file` is kept. User holidays are merged into the regular holiday source
  (`draw.merged_holidays`) and treated exactly like library holidays on every page, day pages included,
  with no separate styling (Phase 12).
- Save writes the grouped block form, and flat and grouped files both load (Phase 10).
- Global and "Colors & styling" are collapsible sections in the same panel. Global previews the full
  agenda. Colors & styling previews the last active template, or the full agenda if there is none
  (Phase 15).
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
