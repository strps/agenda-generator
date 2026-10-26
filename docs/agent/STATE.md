# STATE: agenda-generator        (rewritten each phase, max 80 lines)
Last phase: 01   (plan: export dialog; earlier decisions below still hold)
## Decisions in force
- ExpandingToolTip filters only the top widget (+ viewport); no descendant filters, since Leave fires between children (phase 08)
- help_text.py is Qt-free and plain text (no HTML); it imports only bar_model.SECTION_LABELS, never Config/pydantic (phase 01, 07)
- Tests run via `.venv/bin/python -m pytest` (bare `pytest`/`python` not on PATH); set QT_QPA_PLATFORM=offscreen (phase 01)
- Main toolbar tooltips set once in MainWindow.__init__; `_sync_export_button` sets export tooltip to TOOLTIPS["export_pdf"], plus "\n\n"+EXPORT_DISABLED_REASON when invalid (phase 02)
- Preview nav tooltips set in PreviewWidget.__init__ from TOOLTIPS; mode uses TOOLTIPS[f"mode_{m}"] (KeyError if missing) (phase 03)
- Legend: persistent `Legend.title` QLabel (objectName legend_title) is re-added after each set_entries rebuild, never deleted; button and swatch share tooltip `section_tooltip(key)\nClick to go to the first <Label> page.` (phase 04)
- Padding swatch is a QLabel with a 12x12 QPixmap (gray + BDiagPattern in window color); other swatches use stylesheet background; `recolor()` handles both and runs on PaletteChange (phase 05)
- SectionBar hover: `hover_at(x, global_pos=None)` tracks section key (padding -> B.PADDING); single-shot `expand_timer` (made by hover_tooltip.make_expand_timer) starts only when the section changes; `_expand` appends `help_text.section_tooltip`; `reset_hover()` on leave, press/drag, set_plan, empty space (phase 06)
- Param texts: PARAM_SHORT/PARAM_DETAILS keyed by Config field name, cover every field, details name cross-field rules and list Literal choices; test derives names from Config.model_fields (phase 07)
- SettingsPanel: `tooltips[name]` ExpandingToolTip on every editor (incl. `pages` group box); non-pages rows use explicit QLabel `label_<name>` with `label_tooltips[name]`; attached in __init__ after _make (phase 09)
- Config stays flat; agenda/templates.py groups fields into sections (key mapping only, imports no Config/pydantic). YAML blocks flattened in configfile.flatten; save_yaml writes grouped form, booklet fields stay flat (phase 10)
- Page settings are Config fields (daily_hour_start/end 6/21, schedule_first/last_hour 7/21, habits_max 20, niche_*_pages 1); class constants stay as defaults, `Schedule.layout(rows, max_hours=MAX_HOURS)` and `Habits.layout(rows, max_habits=MAX_HABITS)`; `_Counted(count=None)` falls back to `config.<id>_pages` (phase 11)
- Back matter: `Notes`/`Contacts(count=None)` use config.notes_pages/contacts_pages (default 1, 0 removes); build_plan puts them per instances(config). Padding search starts at `units=config.extra_padding` (limit grows by it); fixed-num_booklets overflow rule applies at units==start; blank fallback unchanged (phase 12)
- Day extras: Config daily_holidays(True)/daily_quotes(False)/daily_quotes_file/daily_extra_file and global holidays_file (all files `Path|None`, validated at config time; relative paths resolve against cwd) (phase 13). `draw.merged_holidays(config)` is the single holiday source (library + holidays_file joined " · "; unsupported country raises ValueError unless file set); holiday_name_for/day_style_for/Holidays page use it; user holidays have no separate style (phase 14)
- Daily header shows "<holiday> · <week>" (truncated, dropped if no room); footer band: quote left (italic), extra text right, each half width when both. File reads cached by (path, mtime[, year]) in draw.py (phase 14)
- Template previews: `sample_plan` ignores planners/pages (disabled templates still preview); daily sample = first day in daily_months; qr uses placeholder URL when qr_urls empty; empty instances (contacts_pages=0) give a `{}` ctx; weekly gets a leading blank filler so it lands on a left/right pair (phase 15)
- Settings panel is one CollapsibleSection per templates.SECTIONS entry (Global expanded, rest collapsed; not an accordion); header enable boxes are views synced from templates.is_enabled on every `changed`; toggling uses with_enabled and writes back only changed editors, emitting `changed` once; `activate(key)` expands (re-entrant via expanded_changed) and emits section_activated once; focus follows QApplication.focusChanged (phase 16)
- Main preview: MainWindow.preview_stack (page 0 = full `preview`, then `template_page_<key>` containers with `template_notice_<key>` + PreviewWidget per TEMPLATE_KEYS). `show_preview_for(key)` (from settings.section_activated; section_bar.page_requested and legend.section_clicked call it with GLOBAL); STYLING keeps last template. Inactive/notice updated for all templates each update_preview; set_plan only on the visible template, others stale until shown; invalid config set_error on all (phase 17)
- Styling: agenda/gui/style_model.py (Qt-free) holds THEMES dark/light, SPACING, stylesheet(dark), contrast_ratio, resolve_dark, APPEARANCES, DEFAULT_APPEARANCE=dark; <=10 hex colors, borders <=1px, no bare QLabel rule. `app.apply_style(app, appearance)` sets QSS + QPalette; main() applies saved appearance, MainWindow() itself does not restyle. Appearance is GUI-only: `settings.appearance_box` (objectName appearance, in STYLING form), signal `appearance_changed`, MainWindow._set_appearance saves to QSettings("agenda-gen","agenda-gui") key appearance only on user change; `MainWindow(prefs=None)` (phase 18)
- Docs: README "Configuration" (Sections/Padding/Day extras) and "GUI", docs/architecture/gui.md, examples/{daily_quotes,daily_extra,holidays}.txt, commented `daily:` block in config.yaml; tests/test_sample_files.py pins config.yaml to the flat sample (booklet_folded field name) (phase 19)
- Cross-field hour rules (start < end) live in Config._check_booklet_rules; each new field needs a CLI option + PARAM_SHORT/DETAILS (phase 11)
- with_enabled on a "page" section with empty pages copies preset_pages(preset) first (phase 10)
- Page numbers: Config page_number_start/first/position/placement/format (flat YAML, validated by numbering.validate_format); label drawn in exporter._draw_number right after add_page (before page content), muted 7pt Inter; margin = centered in bottom margin band, footer = bottom of safe area; total = len(plan); n = page - first + start (phase 01)

## Interfaces
- agenda/numbering.py (Qt-free): `label_for(cfg,page,total)->str|None`, `align_for(side,position)->L|C|R`, `x_for(side,position,safe_x,safe_w,text_w)`, `validate_format(fmt)`; CLI `--page-number-start/-first/-position/-placement/-format`; tests/test_page_numbers.py
- agenda/gui/help_text.py: `TOOLTIPS` (ids open_config, save_config, export_pdf, prev, next, mode_single, mode_spread, mode_sheet, zoom), `EXPORT_DISABLED_REASON`, `SECTION_DESCRIPTIONS`, `section_tooltip(key)`, `PARAM_SHORT`, `PARAM_DETAILS`, `param_tooltip(name, expanded=False)` (short, or short+"\n"+detail; unknown name returns name)
- agenda/gui/hover_tooltip.py: `HOVER_EXPAND_MS=1500` (only definition; re-exported by section_bar), `make_expand_timer(parent, slot)`, `ExpandingToolTip(widget, short, detail)` (event filter on widget + scroll-area viewport; members expand_timer, expanded, hover(global_pos=None), current_text(), reset(), set_texts(short, detail)); Enter starts timer, ToolTip shows current text (consumed; fallback starts timer), Leave/Hide reset; tests/test_gui_hover_tooltip.py
- section_bar.py: `HOVER_EXPAND_MS` (imported), `SectionBar.expand_timer`, `hover_at`, `current_tooltip`, `reset_hover`; tests in tests/test_gui_bar_hover.py
- tests/test_gui_tooltips.py: has module-scoped `qapp` fixture; main toolbar + preview nav tests; toolbar-region check covers win.preview and the toolbar parent of open_button (legend/settings excluded)
- tests/test_gui_settings_tooltips.py: settings editor/label tooltip tests
- tests/test_gui_param_help.py: Qt-free tests for param texts (derive names from Config.model_fields)

- agenda/templates.py: `GLOBAL`, `STYLING`, `SectionSpec(key,label,block,fields,page_id,enable)`, `SECTIONS`, `TEMPLATE_KEYS`, `section`, `group_of`, `fields_of(key, all_fields)`, `is_enabled(cfg,key)`, `has_enable_box`, `with_enabled(values,key,on)`; enable in planner|page|count|none; SectionSpec.count_field for "count" (is_enabled = field>0; with_enabled off=0, on=1 only if 0); contacts section sits after weekly
- agenda/day_extras.py (Qt-free, no Config import): `read_lines(path)`, `parse_dated(lines, year)->dict[date,str]` (entries joined " · "; Feb 29 MM-DD skipped in non-leap years), `builtin_quotes(lang)`, `quote_for(d, quotes)`; tests/test_day_extras.py
- draw.py: `merged_holidays`, `dated_entries(path, year)`, `quotes_for(config)`; day_extras: `JOIN`, `truncate(text, max_width, width_of)`; tests/test_daily_extras.py, tests/test_user_holidays.py
- agenda/gui/template_model.py (Qt-free): `sample_plan(cfg, key, instance=0)->PagePlan` (ValueError for GLOBAL/STYLING/unknown), `preview_mode(key)` (spread if page.pages==2 else single), `preview_target(active, last_template)`, `PLACEHOLDER_URLS`; tests/test_gui_template_model.py
- agenda/gui/collapsible.py: `CollapsibleSection(key,title,enable)` (toggle_button, enable_box|None checked by default, body, form; set_expanded/is_expanded/set_enabled_state/enabled_state; signals expanded_changed, enable_toggled user-only). SettingsPanel: `sections`, `active_section`, `section_activated(str)`, `activate`, `notify_focus`; `pages` box sits in the Global form; tests/test_gui_collapsible.py, test_gui_settings_sections.py
- app.py: `preview_key`, `last_template`, `template_previews`, `template_notices`, `show_preview_for`; PreviewWidget.set_inactive(on)/`inactive` (QGraphicsOpacityEffect 0.35 on scroll; tests/test_gui_template_preview.py)
- settings_model `OPT_PATH` kind (Path|None); SettingsPanel maps "" <-> None
- settings_model.config_to_yaml_data(cfg) grouped dict; config_to_data stays flat; tests/test_templates.py

## Open issues
- footer placement can overlap the day-page quote/extra text in the footer band (not avoided)

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen
