# STATE: agenda-generator
Plan: 2026-10-26-structure-cleanup
Last phase: 02
ADRs: docs/adr/README.md (none yet)
Earlier plans: last legacy STATE (export dialog plan) is `git show 93ed548:docs/agent/STATE.md`.
## Decisions (this plan)
- Ruff unsafe fixes used only in tests (unused unpacked vars renamed `_x`); `subprocess.run(..., check=False)` made explicit: keeps ruff clean without changing behavior (structure-cleanup/01)
- Baseline: 1787 tests collected; tests/data/default_style_fingerprint.json must stay unchanged (structure-cleanup/01)
- Rules carried from earlier plans that later phases rely on (structure-cleanup/01):
  - Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen.
  - help_text.py is Qt-free, plain text; phase 04 relaxes its "no Config import" rule (may import agenda.fields) but never PySide6.
  - agenda/templates.py imports no Config/pydantic and is the only source of section grouping.
  - Config stays flat; YAML blocks flattened in configfile.flatten, save_yaml writes grouped form.
  - Each new field needs CLI option + PARAM_SHORT/DETAILS (phase 05 rewrites this rule).
  - tests/test_sample_files.py pins config.yaml to the flat sample.
- `gui` marker: whole-Qt files set `pytestmark = pytest.mark.gui`; mixed files decorate individual tests. tests/conftest.py ignores files containing that pytestmark when PySide6 is missing (module importorskip removed, else it skips noisily under -m 'not gui'). New Qt test files must use the same pytestmark (structure-cleanup/02)
## Contracts (between this plan's phases)
- PARAM_SHORT, PARAM_DETAILS, param_tooltip: agenda/gui/help_text.py (public names stay)
- CLI flag surface pin: tests/test_cli_flags.py (phase 03, to be created)
## Open issues
- Footer placement can overlap the day-page quote/extra text in the footer band (not avoided)
## Blocked
- none
## Changes this phase (only when phases are not committed)
## Suggested for CLAUDE.md
- Ruff is clean (check + format); keep it so. Run tests with `.venv/bin/python -m pytest` and QT_QPA_PLATFORM=offscreen
