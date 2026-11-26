# STATE: agenda-generator        (working memory of the active plan, rewritten each phase, max 40 lines)
Plan: 2026-11-25-text-fit-warnings
Last phase: 10
ADRs: docs/adr/README.md (long-lived decisions; read the index, open an ADR only when your phase touches it)

## Decisions (this plan)
- fit_text's `width_of(text)` measures at `size_pt` only; widths are scaled linearly by size/size_pt for shrink/wrap, so callers pass a one-arg measurer: keeps fake test measurers trivial and fpdf out of the module (text-fit-warnings/01)
- wrap: size = largest in [min_scale, 1]*size_pt (0.25 pt steps) where max_lines lines fit `height`, else the minimum; line count capped by height at that size; last line is day_extras.truncate of the remainder (text-fit-warnings/01)
- header_text_fit (default overflow) / footer_text_fit (default ellipsis) are separate Config fields in the STYLING section (yaml style:); footer_text_fit now used by Daily._footer, header_text_fit not yet used: header gets the extra "overflow" value, footer cannot (text-fit-warnings/02)
- fit_cell sets the font itself (role/style/unscaled size_pt), measures at pdf.font_size_pt; wrap line height = 1.2 * size; "overflow" = one plain pdf.cell (byte-identical); footer ellipsis stays byte-identical to old truncate+cell (text-fit-warnings/03)
- render_pages logs into a private CutLog and copies only requested pages' entries (multi-page instances are drawn whole) (text-fit-warnings/03)
- Text that fits on one line at size_pt returns unchanged in every mode (text-fit-warnings/01)
- Cut report: agenda/cutreport.py (Qt-free, tr() keys cuts.*); CLI echoes it to stderr after "wrote" (exit 0); ExportSignals.done is now (path, status suffix, full report); MainWindow.export_result = text + report, status bar gets the short suffix, interactive box is a Warning with detailed text (text-fit-warnings/04)
- Daily header: overflow mode keeps today's drawing but logs a shortened/dropped holiday name as a header cut; other modes fit the title in header width minus week label (-4 mm gap), then the holiday (shrink: size from fit_text on the whole right string, then truncate) (text-fit-warnings/05)
- Weekly._page takes keyword-only `config` (needed for header_text_fit) (text-fit-warnings/05)
- Optional and value-added pages: draw_header_title replaces set_font+set_xy+cell (it sets the font itself; caller sets color); _Counted._header now takes `config` as 4th arg (text-fit-warnings/06, 07)
- Preview: RenderSignals.done is now (id, images, CutLog); PreviewWidget keeps per-config CutLog of pages rendered so far (reset on config hash change), shows `warning` label for visible pages, emits cuts_changed(report) which MainWindow appends to the summary tooltip (text-fit-warnings/08)
- back_cover (default False) is the single switch for BackCover in build_plan; `pages` membership ignored. Intentional exception to "existing config.yaml loads to same Config": configs without the key now get no back cover. With separate_covers and no back cover only cover + inside-cover filler are outside booklets (outside_tail = 2 only with back cover) (text-fit-warnings/09)
- Daily._label (classmethod) inset by LABEL_TOP_GAP = SPACING[1]: cell at g.row(row)+gap, height baseline-gap, so titles stay inside their baseline row (text-fit-warnings/10)

## Contracts (between this plan's phases)
- Fitting: agenda/textfit.py::fit_text -> FitResult(lines, size_pt, cut); FIT_MODES, FOOTER_FIT_MODES
- Cut collection: agenda/textfit.py::CutLog (add(page, region, text), entries, pages(region), bool, len); format_ranges(pages) -> "3, 5, 14-20"
- Renderer: agenda/draw.py::fit_cell(pdf,x,y,w,h,text,*,region,mode,role,style,size_pt,align); AgendaPDF.agenda_page_numbers / agenda_cut_log (pdfdoc.py); export_agenda/render_pages(cuts=CutLog|None) (exporter.py)
- Headers: agenda/draw.py::draw_header_title(pdf,g,text,config,size_pt,align,*,width,role,style) (core, optional, value-added pages use it; caller sets text color); fit_cell now returns FitResult|None; draw.py::log_cut(pdf,region,text)
- Report text: agenda/cutreport.py::cut_report_lines(log), cut_status(log) 
- Preview: agenda/gui/preview_model.py::cut_warning(log, plan indices), cuts_tooltip(log); preview.py::PreviewWidget.warning / cuts
- Back cover: agenda/config.py::Config.back_cover; agenda/assembler.py::build_plan try_padding/outside_tail
- Region ids: "header", "footer"
- Options: agenda/config.py::Config.header_text_fit / footer_text_fit (Literal types; CLI --header-text-fit/--footer-text-fit)

## Open issues
- none

## Blocked
- none

## Changes this phase (only when phases are not committed)

## Suggested for CLAUDE.md
- none
