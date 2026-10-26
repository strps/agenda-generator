# PLAN: Structure cleanup

Plan: 2026-10-26-structure-cleanup
Closed: 2026-10-26
Goal: Make ruff clean, split fast core tests from GUI tests, make Config fields the single source of per-field help and CLI flag metadata (help_text and the CLI derived from it), and split the large page modules value_added.py and optional.py into packages, all without changing behavior or PDF output.
Backlog: -
Out of scope: nested Config sub-models; any change to PDF output (must stay byte/fingerprint identical); GUI behavior changes; YAML format changes; moving section grouping out of agenda/templates.py; new dependencies; docs reorganization beyond updating README/docs/architecture text that describes changed code; anything under .claude/, CLAUDE.md, docs/adr, BACKLOG.md
Stack: Python 3.11+, PySide6 GUI (agenda/gui/), fpdf2 + pypdf PDF generation, pytest
Verify command: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
Constraints: no new dependencies; keep existing GUI models and public API stable; every existing config.yaml must keep loading to the same Config; Qt-free logic lives in Qt-free modules (e.g. agenda/gui/export_model.py) and is tested without PySide6; every new option gets a tooltip (help_text) and a CLI equivalent where one is missing
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
Only the run-plan orchestrator changes status tags.
-->

<!--
Planner findings (2026-10-26):
- Previous plan "Export dialog" (13 phases, all PASS) replaced at the user's request; it is in git history.
- Verify fails today only on ruff: 59 `ruff check` errors (mostly unused `# noqa`) and 18 files that
  `ruff format --check` would reformat. Tests pass.
- PySide6 usage in tests is only in tests/test_gui_*.py. Three patterns:
  (1) module-level `pytest.importorskip("PySide6")`: test_gui_tooltips, test_gui_style_editors,
      test_gui_bar_hover, test_gui_template_preview, test_gui_settings_tooltips, test_gui_hover_tooltip,
      test_gui_settings_sections, test_gui_collapsible;
  (2) plain top-level `from PySide6 ...` with no skip: test_gui_export_dialog, test_gui_style
      (check test_gui_prefs_dialog too);
  (3) mixed files where only some tests call importorskip inside the test: test_gui_legend,
      test_gui_settings, test_gui_colors, test_gui_export, test_gui_shell, test_gui_export_flow,
      test_gui_bar, test_gui_preview.
  Qt-free: test_gui_export_model, test_gui_param_help, test_gui_template_model, test_gui_help_text,
  test_gui_style_model (no PySide6 import).
- cli.run has 71 hand-written options. Non-field options (stay hand-written): --version, --list,
  --config, --category, --page-range, --blank-pages, --dry-run. Field options with a special form:
  --page-size/--size, --booklet-size/--booklet, --booklet-unit/--unit, --folded/--flat
  (booklet_folded), --debug-grid (bool, no --no form), -o/--output, --qr-url (repeatable,
  field qr_urls), comma-list strings planners/month_start_pages/month_end_pages/pages
  (pages merged with --category), num_booklets as str (int-or-"auto"), daily_months as str
  (Config parses it), Literal fields are typed `str` on the CLI (Config validates -> exit 2).
  Every CLI default is None (False for the eager/flag-only options).
- help_text.py PARAM_SHORT/PARAM_DETAILS (lines ~139-485) cover every Config field; used by
  settings_panel.py, export_dialog.py, param_tooltip, tests/test_gui_param_help.py,
  tests/test_gui_settings_tooltips.py, tests/test_gui_export_model.py.
- value_added.py: 15 page classes (MonthlyQuotes, VisionBoard, HealthTracker, Meals, Gratitude, Media,
  Travel, Challenge30, IdeaMap, QRCodes, ExtrasGuide, PackEntrepreneur, PackStudent, PackFitness)
  + NamedTuple layouts + helpers `_fit`, `_Counted`. optional.py: 10 classes (Goals, ImportantDates,
  Todo, Projects, Budget, Habits, MonthlyReview, Schedule, Holidays, Passwords) + `_draw_task_list`,
  `_ellipsize`. catalog.PAGE_MODULES imports "agenda.pages.optional" / "agenda.pages.value_added";
  registration order = import order of the @register decorators. tests/test_gui_colors.py iterates
  `vars(value_added)` / `vars(optional)` for `section` attributes; tests import classes from both modules.
-->

## Phase 01 — Ruff clean   [status: done]
Deliverable: `ruff check agenda tests` and `ruff format --check agenda tests` both pass; no behavior change.
Files: whatever ruff reports under agenda/ and tests/ (about 18 reformatted files plus noqa/lint fixes); no other files
Depends on: none
Done when: .venv/bin/ruff check agenda tests && .venv/bin/ruff format --check agenda tests && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest passes, and tests/data/default_style_fingerprint.json is unchanged (`git diff --quiet -- tests/data` exits 0) and no test file was deleted or had a test removed (same `pytest --collect-only -q | tail -1` count as before the phase).
Notes: Mechanical phase, so the file count may exceed 10. Use `ruff check --fix` (unused noqa is RUF100; `ruff check --fix` handles it) then `ruff format`; fix whatever is left by hand. Do not add a `[tool.ruff.lint]` select/ignore that hides real errors; a narrow per-file ignore is allowed only with a one-line comment saying why. Do not change runtime logic. If `from PySide6 ...` imports after `importorskip` lose their `# noqa: E402` and E402 then fires, keep the noqa (it is used). Record the collect count before you start.
Review: FAIL -> fixed -> PASS

## Phase 02 — `gui` pytest marker   [status: done]
Deliverable: A registered pytest marker `gui` on every test that needs PySide6, so `-m "not gui"` runs the Qt-free core; the plain Verify run still runs everything.
Files: pyproject.toml, tests/test_gui_*.py that use PySide6 (see findings), README.md (one line in the testing/dev section)
Depends on: 01
Done when: the Verify command passes; `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --strict-markers -q` passes; and `.venv/bin/python -c "import sys; sys.modules['PySide6']=None; import pytest; sys.exit(pytest.main(['-m','not gui','-q','-rs','-p','no:cacheprovider']))"` exits 0 with no skip reason mentioning PySide6 in its output (that proves every Qt test is marked and every unmarked test is Qt-free).
Notes: Register in `[tool.pytest.ini_options]` as `markers = ["gui: needs PySide6 (deselect with -m 'not gui')"]` and add `--strict-markers` to addopts only if it does not break anything. Files that are Qt-only get `pytestmark = pytest.mark.gui`. In mixed files, mark only the tests that call `importorskip("PySide6")` or use a Qt fixture (decorator `@pytest.mark.gui`); leave Qt-free tests in those files unmarked. Qt-free files (test_gui_export_model, test_gui_param_help, test_gui_template_model, test_gui_help_text, test_gui_style_model) stay unmarked. Subprocess checks such as test_no_qt_import stay unmarked. Keep the existing importorskip calls so machines without PySide6 still skip.
Review: PASS

## Phase 03 — Pin the CLI flag surface   [status: done]
Deliverable: tests/test_cli_flags.py pins the current CLI interface as literal data, written against the hand-written cli.py before any refactor. For every click parameter of `typer.main.get_command(cli.app)` it pins: param name, `opts`, `secondary_opts`, `default`, `is_flag`, `multiple`, and the click type name. It also pins the map Config field -> CLI param (every Config field appears; qr_urls -> qr_url; pages -> pages plus category).
Files: tests/test_cli_flags.py (new)
Depends on: 01
Done when: the Verify command passes; tests/test_cli_flags.py contains the expected table as a literal (no value computed from cli.py), and a test there asserts `set(Config.model_fields)` is covered exactly by the pinned field map (no field missing, no extra).
Notes: Test-only phase; no production code changes. Generate the literal once with a throwaway script (in the scratchpad), paste it into the test, and compare whole dicts so one diff names every changed flag. Exclude only `help` text from the pin, because phase 05 replaces it on purpose. Also pin `main(["--help"]) == 0` and that `main(["--year", "abc"])` returns the same exit code as today (typer usage error, 2).
Review: PASS

## Phase 04 — Field help metadata on Config   [status: done]
Deliverable: Every Config field carries its own help: short text as `Field(description=...)` and detailed text plus CLI metadata in `json_schema_extra={"detail": ..., "cli": {...}}`. A new Qt-free core module agenda/fields.py reads them: `short_help(name)`, `detail_help(name)`, `cli_meta(name)`, `field_names()` (Config field order). agenda/gui/help_text.py keeps its public names `PARAM_SHORT`, `PARAM_DETAILS`, `param_tooltip`, now built from agenda.fields; the hand-written dicts are gone from gui/.
Files: agenda/config.py, agenda/fields.py (new), agenda/gui/help_text.py, tests/test_fields.py (new), tests/test_gui_help_text.py, docs/architecture/gui.md, docs/agent/STATE.md
Depends on: 03
Done when: the Verify command passes; `PARAM_SHORT` and `PARAM_DETAILS` hold exactly the same keys and texts as before (pin: in this phase, before editing, dump both dicts to tests/data/param_help.json and add a test comparing them; delete nothing from that file later); a test in tests/test_fields.py asserts that no field's short or detail text occurs in the source of agenda/gui/help_text.py (texts live only on Config); `.venv/bin/python -c "import sys, agenda.fields; assert not any(m.startswith('PySide6') for m in sys.modules)"` exits 0; tests/test_configfile.py, tests/test_sample_files.py and the style fingerprint test pass unchanged.
Notes: Decision: relax the old rule "help_text imports only bar_model.SECTION_LABELS, never Config/pydantic" (STATE.md decision list). help_text may now import agenda.fields (which imports agenda.config/pydantic); it must still never import PySide6, and test_no_qt_import keeps checking that. agenda/templates.py keeps its rule (imports no Config/pydantic) and stays the only source of section grouping. Update the STATE.md decision line for help_text accordingly. Fields that use a bare default (`orientation: Literal[...] = "portrait"`) become `Field("portrait", description=...)`; defaults, default_factory, ge/le and validators must stay identical (check `Config().model_dump()` and `Config.model_json_schema()` constraints are unchanged apart from description/extra keys). The `cli` dict schema, used in phase 05, is: `flags` (list of option strings, e.g. ["--page-size", "--size"] or ["--folded/--flat"]; omitted = derived `--<name-with-dashes>`, plus `--x/--no-x` for bool), `type` (override CLI type, e.g. "str" for Literal and int|"auto"), `csv` (bool: comma list -> list via split_csv), `skip` (bool: option is hand-written in cli.py, e.g. pages, qr_urls, output if kept special). Fill `cli` for every field in this phase, using the phase 03 pin as the reference, even though cli.py does not read it yet. Moving ~350 lines of text into config.py is expected; keep each field's texts next to the field.
Review: PASS

## Phase 05 — Generate CLI options from Config   [status: done]
Deliverable: cli.py builds the options for all simple Config fields from agenda.fields (flag names, type, default None, bool `--x/--no-x` forms, help = short help text); only the non-field and special options stay hand-written. `build_overrides` keeps its signature and behavior.
Files: agenda/cli.py, agenda/fields.py, agenda/config.py (only `cli` metadata fixes), tests/test_cli_flags.py, README.md (short "adding a Config field" note), docs/agent/STATE.md
Depends on: 04
Done when: the Verify command passes, including tests/test_cli.py, tests/test_cli_flags.py (phase 03 pin unchanged except for help text), tests/test_gui_export.py and tests/test_gui_export_model.py parity tests; a new test in tests/test_cli_flags.py asserts that for every generated param `param.help == fields.short_help(field)`; `grep -c "typer.Option(" agenda/cli.py` is at most 12.
Notes: Suggested approach: keep a `run(**kwargs)` body and give it a generated `inspect.Signature` whose parameters are `Annotated[<type> | None, typer.Option(*flags, help=...)]` with default None; set `run.__signature__` (and `run.__annotations__`) before `app.command()(run)`. Pitfall: typer also calls `typing.get_type_hints`; check the generated annotations reach typer, otherwise build the click params via `typer.models.OptionInfo` directly. Keep the hand-written options and their order first (--version, --list, --config), then generated ones in Config field order, then --category, --page-range, --blank-pages, --dry-run. Exit codes stay: ValueError from Config -> 2, FontsMissingError -> 1, usage errors -> typer's 2. Literal fields stay `str` on the CLI (no click.Choice), so invalid values still go through Config and the same messages. In STATE.md replace the line "each new field needs a CLI option + PARAM_SHORT/DETAILS" with: a new field needs description/detail/cli metadata on Config, the templates.SECTIONS entry, the settings_model kind only if special, and docs.
Review: PASS

## Phase 06 — Split value_added.py into a package   [status: done]
Deliverable: agenda/pages/value_added/ package with one module per page (monthly_quotes, vision_board, health, meals, gratitude, media, travel, challenge30, idea_map, qr_codes, extras_guide, pack_entrepreneur, pack_student, pack_fitness) plus a private shared module for `_fit` and `_Counted`; `__init__.py` imports the page modules in the original order and re-exports every public name (page classes and *Layout NamedTuples) with `__all__`. agenda/pages/value_added.py is deleted.
Files: agenda/pages/value_added.py (deleted), agenda/pages/value_added/*.py (new), tests/test_catalog_order.py (new), docs/architecture/*.md only if they name the file
Depends on: 01
Done when: the Verify command passes (all existing `from agenda.pages.value_added import X` tests, test_smoke, test_gui_colors, test_presets, the style fingerprint test); tests/test_catalog_order.py, written before the move, pins the full ordered list of catalog page ids and every preset's page list as literals and passes after the move; `test ! -e agenda/pages/value_added.py`; every new module is under 300 lines (`wc -l agenda/pages/value_added/*.py`).
Notes: Mechanical move, so the file count exceeds 10. Write and run tests/test_catalog_order.py first (against the old module), then move code without editing it. Use `git mv` for the first module so history follows. Each module keeps `from __future__ import annotations` and imports only what it uses (ruff F401 will tell). Registration happens at import, so `__init__.py` must import the page modules in exactly the old class order; ruff's isort (I001) is not enabled today, but if it is, add `# noqa: I001` with a comment. catalog.PAGE_MODULES stays unchanged.
Review: PASS

## Phase 07 — Split optional.py into a package   [status: done]
Deliverable: agenda/pages/optional/ package with one module per page (goals, important_dates, todo, projects, budget, habits, monthly_review, schedule, holidays, passwords) plus a private shared module for `_draw_task_list` and `_ellipsize`; `__init__.py` imports them in the original order and re-exports all public names. agenda/pages/optional.py is deleted.
Files: agenda/pages/optional.py (deleted), agenda/pages/optional/*.py (new), tests/test_catalog_order.py (unchanged), docs/architecture/*.md only if they name the file
Depends on: 06
Done when: the Verify command passes (including tests/test_catalog_order.py unchanged from phase 06, all `from agenda.pages.optional import X` tests, test_gui_colors, test_smoke, the style fingerprint test); `test ! -e agenda/pages/optional.py`; every new module is under 300 lines.
Notes: Same rules as phase 06. Do not edit tests/test_catalog_order.py; a needed edit there means the order changed, which is a bug.
Review: PASS
