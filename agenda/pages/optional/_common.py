"""Helpers shared by the optional pages."""

from __future__ import annotations

from fpdf import FPDF

from agenda import tokens
from agenda.draw import color, draw_checkbox, font
from agenda.grid import Grid


def _draw_task_list(
    pdf: FPDF, g: Grid, row: int, n: int, labels: tuple[str, str], box: float, due_cols: int
) -> None:
    """Label row at baseline row ``row``, then ``n`` rows of checkbox + task rule + due rule.

    The due column is the last ``due_cols`` grid columns; the task rule ends one gutter before.
    """
    x = g.safe.x
    dx, dw = g.col(g.columns - due_cols, due_cols)
    task_w = dx - g.gutter - x
    box = min(box, g.baseline - 1.0)
    pdf.set_text_color(*color(pdf, "muted"))
    pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
    pdf.set_xy(x, g.row(row))
    pdf.cell(task_w, g.baseline, labels[0])
    pdf.set_xy(dx, g.row(row))
    pdf.cell(dw, g.baseline, labels[1])
    pdf.set_draw_color(*color(pdf, "line"))
    pdf.set_line_width(tokens.STROKE_HAIRLINE)
    for k in range(n):
        top, y = g.row(row + 1 + k), g.row(row + 2 + k)
        draw_checkbox(pdf, x, top + (g.baseline - box) / 2, box)
        pdf.line(x + box + 2, y, x + task_w, y)
        pdf.line(dx, y, dx + dw, y)


def _ellipsize(pdf: FPDF, text: str, width: float) -> str:
    """``text`` cut to fit ``width`` in the current font, ending in "..." when cut."""
    if pdf.get_string_width(text) <= width:
        return text
    while text and pdf.get_string_width(text + "...") > width:
        text = text[:-1]
    return text.rstrip() + "..."
