"""Drawing helpers on top of fpdf2 (lines, boxes, patterns)."""

from __future__ import annotations

from fpdf import FPDF

from agenda.grid import Grid

_INNER_FILL = (200, 220, 255)  # blue: inner (binding) margin
_OUTER_FILL = (255, 225, 190)  # orange: outer margin
_BOX = (120, 120, 120)
_COL_FILL = (255, 190, 215)
_BASELINE = (150, 200, 235)
_RULER = (90, 90, 90)


def _ruler_ticks(pdf: FPDF, length: float, vertical: bool) -> None:
    """Ticks every 1/5/10 mm along one page edge (top or left); labels every 10 mm."""
    pdf.set_draw_color(*_RULER)
    pdf.set_text_color(*_RULER)
    pdf.set_line_width(0.1)
    pdf.set_font("Inter", "", 4)
    for mm in range(int(length) + 1):
        size = 3.0 if mm % 10 == 0 else 2.0 if mm % 5 == 0 else 1.0
        if vertical:
            pdf.line(0, mm, size, mm)
        else:
            pdf.line(mm, 0, mm, size)
        if mm % 10 == 0 and mm:
            if vertical:
                pdf.text(3.4, mm + 0.5, str(mm))
            else:
                pdf.text(mm - 1.0, 5.2, str(mm))


def draw_debug_grid(pdf: FPDF, grid: Grid, page_no: int | None = None) -> None:
    """Overlay margins (inner blue / outer orange), header/content/footer boxes, columns,
    5 mm baseline rules and mm rulers on the current page. Restores graphics state."""
    w, h, s = grid.page_w, grid.page_h, grid.safe
    pdf.set_fill_color(*_INNER_FILL)
    pdf.set_draw_color(*_BOX)
    with pdf.local_context(fill_opacity=0.5, stroke_opacity=0.9):
        if grid.side == "left":
            inner_x, outer_x = w - grid.inner, 0
        else:
            inner_x, outer_x = 0, w - grid.outer
        pdf.set_fill_color(*_INNER_FILL)
        pdf.rect(inner_x, 0, grid.inner, h, style="F")
        pdf.set_fill_color(*_OUTER_FILL)
        pdf.rect(outer_x, 0, grid.outer, h, style="F")
        # top/bottom margin bands in the neutral tint
        pdf.set_fill_color(235, 235, 235)
        pdf.rect(s.x, 0, s.w, grid.top, style="F")
        pdf.rect(s.x, s.y2, s.w, grid.bottom, style="F")

        # columns with gutters
        pdf.set_fill_color(*_COL_FILL)
        with pdf.local_context(fill_opacity=0.25):
            for i in range(grid.columns):
                pdf.rect(grid.col_x(i), grid.content.y, grid.col_width, grid.content.h, style="F")

        # baseline rules every 5 mm over the content box
        pdf.set_draw_color(*_BASELINE)
        pdf.set_line_width(0.1)
        for n in range(grid.rows + 1):
            y = grid.row(n)
            pdf.line(s.x, y, s.x2, y)

        # safe area, header, content, footer outlines
        pdf.set_draw_color(*_BOX)
        pdf.set_line_width(0.2)
        pdf.rect(s.x, s.y, s.w, s.h)
        pdf.set_line_width(0.1)
        for r in (grid.header, grid.content, grid.footer):
            pdf.rect(*r)

    # rulers and label (opaque thin ink)
    pdf.set_line_width(0.1)
    _ruler_ticks(pdf, w, vertical=False)
    _ruler_ticks(pdf, h, vertical=True)
    pdf.set_text_color(*_RULER)
    pdf.set_font("Inter", "B", 6)
    label = f"{'p.' + str(page_no) + ' ' if page_no else ''}{grid.side} page  inner {grid.inner:g} / outer {grid.outer:g} mm"
    pdf.text(s.x + 6, s.y + 4, label)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(0, 0, 0)
    pdf.set_line_width(0.2)
