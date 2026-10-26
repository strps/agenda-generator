# PLAN: no active plan

Plan: none
Goal: -
Backlog: -
Out of scope: -
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
