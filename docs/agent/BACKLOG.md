# BACKLOG

One line per idea: `- [ ] [feature|bug|refactor] <text>`. Capture cheaply, plan later.
- Plan one: `@phase-planner plan backlog item <text>`. The planner appends `→ plan <id>`; /close-plan ticks it.
- Small ones need no plan: commit, then tick it with the hash: `- [x] [bug] <text> (abc1234)`.

- [x] [feature] App internationalization (i18n): translatable GUI/CLI strings and localized output → plan 2026-10-26-ui-i18n
- [ ] [bug] Footer placement can overlap the day-page quote/extra text in the footer band (from 2026-10-26-structure-cleanup)
- [ ] [refactor] Remove the unused English "pad uses" text in template_model.PAD_FIELDS (from 2026-10-26-ui-i18n)
- [ ] [bug] tests/test_gui_prefs_dialog.py:53 tooltip assertion is tautological; check the language tooltip text (from 2026-10-26-ui-i18n)
- [ ] [feature] Translate Config/pydantic validation messages and agenda/configfile.py errors (from 2026-10-26-ui-i18n)
- [ ] [feature] Translate the assembler summary line (GUI summary bar, --dry-run) and --list page titles (from 2026-10-26-ui-i18n)
- [ ] [bug] Test runs leave agenda.pdf in the repo root; write to tmp_path or ignore it (from 2026-10-26-ui-i18n)
