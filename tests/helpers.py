"""Shared test helpers for page classes (see docs/plan/phase3-handoff.md)."""

from __future__ import annotations

import io

from pypdf import PdfReader

from agenda.config import Config
from agenda.exporter import add_page, new_document
from agenda.grid import Grid

PT = 25.4 / 72  # mm per PDF point
_EPS = 0.05  # mm tolerance


def render_page(page_cls, config: Config | None = None) -> bytes:
    """Render every instance of ``page_cls`` (new_document -> add_page x pages -> draw)."""
    cfg = config or Config()
    page = page_cls()
    pdf = new_document(cfg)
    for ctx in page.instances(cfg):
        grids = [add_page(pdf, cfg) for _ in range(page.pages)]
        page.draw(pdf, ctx, cfg, grids)
    return bytes(pdf.output())


def drawn_points(pdf_bytes: bytes) -> list[list[tuple[float, float]]]:
    """Per page, (x, y) in mm (origin top-left) of text origins and path/rect corners drawn."""
    out: list[list[tuple[float, float]]] = []
    for pg in PdfReader(io.BytesIO(pdf_bytes)).pages:
        h = float(pg.mediabox.height)
        pts: list[tuple[float, float]] = []

        def add(cm, x, y, pts=pts, h=h):
            ux = cm[0] * x + cm[2] * y + cm[4]
            uy = cm[1] * x + cm[3] * y + cm[5]
            pts.append((ux * PT, (h - uy) * PT))

        def on_op(op, args, cm, tm, add=add):
            if op == b"re":
                x, y, w, hh = (float(a) for a in args)
                for dx, dy in ((0, 0), (w, 0), (0, hh), (w, hh)):
                    add(cm, x + dx, y + dy)
            elif op in (b"m", b"l"):
                add(cm, float(args[0]), float(args[1]))

        def on_text(text, cm, tm, fd, fs, add=add):
            if text.strip():
                add(cm, tm[4], tm[5])

        pg.extract_text(visitor_operand_before=on_op, visitor_text=on_text)
        out.append(pts)
    return out


def assert_in_safe_area(
    pdf_bytes: bytes,
    config: Config | None = None,
    allow_blank: bool = False,
    x_slack: float = 0.0,
) -> None:
    """Assert all drawn points lie inside each page's safe area (needs debug_grid False).

    Checks text origins (not their right edge) and rect/line vertices.
    ``allow_blank`` tolerates empty pages (e.g. a leading filler page).
    ``x_slack`` (mm) lets points sit that far past the left/right edges: title backgrounds grow
    outward by ``config.title_padding`` on purpose.
    """
    cfg = config or Config()
    assert not cfg.debug_grid, "debug grid draws in the margins"
    for n, pts in enumerate(drawn_points(pdf_bytes), start=1):
        s = Grid.for_page(cfg, n).safe
        if allow_blank and not pts:
            continue
        assert pts, f"page {n}: nothing drawn"
        for x, y in pts:
            dx = _EPS + x_slack
            assert s.x - dx <= x <= s.x2 + dx and s.y - _EPS <= y <= s.y2 + _EPS, (
                f"page {n}: ({x:.2f}, {y:.2f}) outside safe {tuple(round(v, 2) for v in s)}"
            )
