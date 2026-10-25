"""Page reordering for booklet printing (Qt-free, pure logic)."""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pypdf import PdfReader, PdfWriter


def imposition_order(n: int) -> list[tuple[int, int]]:
    """Print order of a folded (saddle-stitch) booklet of ``n`` pages.

    ``n`` must be a multiple of 4 (0 gives no sides). Returns the sheet sides in print order,
    each as a ``(left, right)`` pair of 1-based booklet page numbers: sheet ``s`` (1-based)
    has front ``(n-2s+2, 2s-1)`` then back ``(2s, n-2s+1)``. Every pair sums to ``n + 1``.
    """
    if n < 0 or n % 4:
        raise ValueError(f"booklet page count must be a non-negative multiple of 4, got {n}")
    sides: list[tuple[int, int]] = []
    for i in range(n // 4):
        sides.append((n - 2 * i, 2 * i + 1))  # front
        sides.append((2 * i + 2, n - 2 * i - 1))  # back
    return sides


# ---------------------------------------------------------------- 2-up placement (pypdf)

MM_PT = 72 / 25.4
# Landscape sheets (width, height) in mm, tried in this order (letter wins ties).
SHEETS: dict[str, tuple[float, float]] = {"letter": (279.4, 215.9), "a4": (297.0, 210.0)}


def choose_sheet(page_w: float, page_h: float) -> tuple[float, float]:
    """Landscape letter or A4 (mm) giving the larger scale for two ``page_w x page_h`` pages."""
    return max(SHEETS.values(), key=lambda s: placement_scale(page_w, page_h, *s))


def placement_scale(page_w: float, page_h: float, sheet_w: float, sheet_h: float) -> float:
    """Scale (<= 1, never enlarges) so two pages fit side by side on the sheet."""
    return min(1.0, sheet_w / 2 / page_w, sheet_h / page_h)


def place_two_up(
    page_w: float, page_h: float, sheet_w: float, sheet_h: float
) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """Where two pages go on a sheet (any one unit, y up, origin bottom-left of the sheet).

    Returns ``(scale, left_origin, right_origin)``: the lower-left corner of each scaled page.
    Each page is centred in its half of the sheet, so the fold stays at the sheet's middle.
    """
    s = placement_scale(page_w, page_h, sheet_w, sheet_h)
    w, h = page_w * s, page_h * s
    y = (sheet_h - h) / 2
    half = sheet_w / 2
    return s, ((half - w) / 2, y), (half + (half - w) / 2, y)


def impose_pages(
    reader: PdfReader,
    sides: Sequence[tuple[int | None, int | None]],
    sheet_mm: tuple[float, float] | None = None,
    writer: PdfWriter | None = None,
) -> PdfWriter:
    """Add (to ``writer`` or a new one) one landscape sheet side per ``(left, right)`` pair of 1-based ``reader`` pages.

    ``None`` leaves that half blank. The sheet is ``sheet_mm`` or ``choose_sheet`` of the first
    source page; pages are scaled/centred by ``place_two_up`` (sizes taken per page in points).
    """
    from pypdf import PdfWriter, Transformation

    writer = writer or PdfWriter()
    first = reader.pages[0]
    pw, ph = float(first.mediabox.width), float(first.mediabox.height)
    sw, sh = sheet_mm or choose_sheet(pw / MM_PT, ph / MM_PT)
    sw, sh = sw * MM_PT, sh * MM_PT
    for pair in sides:
        sheet = writer.add_blank_page(sw, sh)
        for num, origin_idx in zip(pair, (1, 2)):
            if num is None:
                continue
            src = reader.pages[num - 1]
            w, h = float(src.mediabox.width), float(src.mediabox.height)
            s, *origins = place_two_up(w, h, sw, sh)
            x, y = origins[origin_idx - 1]
            ctm = Transformation().translate(-float(src.mediabox.left), -float(src.mediabox.bottom))
            sheet.merge_transformed_page(src, ctm.scale(s).translate(x, y))
    return writer


def impose_booklets(pdf: bytes, booklet_of: Sequence[int | None]) -> bytes:
    """Impose a finished PDF; ``booklet_of[i]`` is the booklet index of page ``i`` (None = not in one).

    Each booklet (pages contiguous, padded with blanks to a multiple of 4) becomes its sheet sides
    in ``imposition_order``. Pages outside any booklet (separate covers) are kept as they are,
    at their place relative to the booklets (before the first / after the last).
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf))
    if len(reader.pages) != len(booklet_of):
        raise ValueError("booklet_of must have one entry per PDF page")
    groups: dict[int, list[int]] = {}
    for i, b in enumerate(booklet_of):
        if b is not None:
            groups.setdefault(b, []).append(i + 1)
    out = PdfWriter()
    first = min((g[0] for g in groups.values()), default=len(booklet_of) + 1)
    plain = [i + 1 for i, b in enumerate(booklet_of) if b is None]
    for n in (n for n in plain if n < first):
        out.add_page(reader.pages[n - 1])
    for _, pages in sorted(groups.items()):
        padded: list[int | None] = [*pages, *[None] * (-len(pages) % 4)]
        sides = [(padded[a - 1], padded[b - 1]) for a, b in imposition_order(len(padded))]
        impose_pages(reader, sides, writer=out)
    for n in (n for n in plain if n > first):
        out.add_page(reader.pages[n - 1])
    buf = io.BytesIO()
    out.write(buf)
    return buf.getvalue()
