# ADR 0008: Header and footer text fitting, and reporting cut text by agenda page

- Status: Accepted
- Date: 2026-11-26
- Plan: 2026-11-25-text-fit-warnings (text-fit-warnings/01, 02, 03, 04, 05)

## Context
Page header and footer text that is too long for its band used to overflow or be shortened silently.
Users needed to choose how it is fitted and to learn which pages lost text, from the CLI, the GUI
export and the preview, without changing default output or the public export API.

## Decision
- Fitting logic lives in agenda/textfit.py (fit_text, CutLog), which imports neither fpdf nor Qt, so
  GUI, CLI and tests can use and format it; report text is built in Qt-free agenda/cutreport.py via tr().
- Two separate Config fields: header_text_fit (overflow | ellipsis | shrink | wrap, default overflow)
  and footer_text_fit (ellipsis | shrink | wrap, default ellipsis). Both defaults reproduce the old
  output byte for byte. "overflow" is header-only: it draws the title unchanged and is never reported.
- Exception: the Daily header's holiday name was already shortened before this plan, so a shortened or
  dropped holiday name is logged as a header cut in every mode, including overflow.
- Cuts are recorded with real agenda page numbers (AgendaPDF.agenda_page_numbers), never sheet or
  document page numbers, including for partial renders and imposition.
- export_agenda / render_pages only gain an optional keyword `cuts: CutLog | None`; return types are
  unchanged. With cuts=None nothing is collected.
- Cuts are a warning: the CLI prints the report to stderr and still exits 0.

## Consequences
New header/footer text must be drawn through agenda/draw.py's fit_cell / draw_header_title so the
option applies and cuts are logged. Any change to the default modes must keep existing stream-equality
tests green. Content-area text (day-row labels, value-added labels) is not covered; extending fitting
there needs a new decision.
