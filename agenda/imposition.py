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


def choose_sheet(page_w: float, page_h: float, inset: float = 0.0) -> tuple[float, float]:
    """Landscape letter or A4 (mm) giving the larger scale for two ``page_w x page_h`` pages."""
    return max(SHEETS.values(), key=lambda s: placement_scale(page_w, page_h, *s, inset))


def placement_scale(
    page_w: float, page_h: float, sheet_w: float, sheet_h: float, inset: float = 0.0
) -> float:
    """Scale (<= 1, never enlarges) so two pages fit side by side on the sheet.

    ``inset`` reserves that much (same unit) around each scaled page for bleed and crop marks.
    """
    return min(1.0, (sheet_w / 2 - 2 * inset) / page_w, (sheet_h - 2 * inset) / page_h)


MARK_LEN_MM = 3.0  # length of each crop mark
MARK_WIDTH_PT = 0.25


def marks_inset(bleed: float, mark_len: float = MARK_LEN_MM) -> float:
    """Space (bleed + mark length) a page needs on each side so its marks fit."""
    return bleed + mark_len


def crop_mark_segments(
    x: float, y: float, w: float, h: float, bleed: float, length: float = MARK_LEN_MM
) -> list[tuple[float, float, float, float]]:
    """The 8 crop-mark lines ``(x1, y1, x2, y2)`` of the trim box at ``(x, y)`` sized ``w x h``.

    Two per corner, along the trim edges' extensions, starting ``bleed`` outside the trim and
    running ``length`` further out. Any one unit, y up.
    """
    a, b = bleed, bleed + length
    segs = []
    for cx, dx in ((x, -1), (x + w, 1)):
        for cy, dy in ((y, -1), (y + h, 1)):
            segs.append((cx + dx * a, cy, cx + dx * b, cy))  # horizontal
            segs.append((cx, cy + dy * a, cx, cy + dy * b))  # vertical
    return segs


def place_two_up(
    page_w: float, page_h: float, sheet_w: float, sheet_h: float, inset: float = 0.0
) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """Where two pages go on a sheet (any one unit, y up, origin bottom-left of the sheet).

    Returns ``(scale, left_origin, right_origin)``: the lower-left corner of each scaled page.
    Each page is centred in its half of the sheet, so the fold stays at the sheet's middle.
    ``inset`` reserves room around each page for crop marks (see ``placement_scale``).
    """
    s = placement_scale(page_w, page_h, sheet_w, sheet_h, inset)
    w, h = page_w * s, page_h * s
    y = (sheet_h - h) / 2
    half = sheet_w / 2
    return s, ((half - w) / 2, y), (half + (half - w) / 2, y)


def impose_pages(
    reader: PdfReader,
    sides: Sequence[tuple[int | None, int | None]],
    sheet_mm: tuple[float, float] | None = None,
    writer: PdfWriter | None = None,
    bleed_mm: float | None = None,
) -> PdfWriter:
    """Add (to ``writer`` or a new one) one landscape sheet side per ``(left, right)`` pair of 1-based ``reader`` pages.

    ``None`` leaves that half blank. The sheet is ``sheet_mm`` or ``choose_sheet`` of the first
    source page; pages are scaled/centred by ``place_two_up`` (sizes taken per page in points).
    ``bleed_mm`` not None draws crop marks around every placed page (``bleed_mm`` outside the
    trim, ``MARK_LEN_MM`` long) and shrinks the pages to leave room for them. The source pages
    carry no art beyond the trim, so the bleed is only the gap before each mark.
    """
    from pypdf import PdfWriter, Transformation

    writer = writer or PdfWriter()
    first = reader.pages[0]
    pw, ph = float(first.mediabox.width), float(first.mediabox.height)
    marks = bleed_mm is not None
    inset_mm = marks_inset(bleed_mm) if bleed_mm is not None else 0.0
    sw, sh = sheet_mm or choose_sheet(pw / MM_PT, ph / MM_PT, inset_mm)
    sw, sh = sw * MM_PT, sh * MM_PT
    inset = inset_mm * MM_PT
    ops: list[str] = []
    for pair in sides:
        sheet = writer.add_blank_page(sw, sh)
        for num, origin_idx in zip(pair, (1, 2)):
            if num is None:
                continue
            src = reader.pages[num - 1]
            w, h = float(src.mediabox.width), float(src.mediabox.height)
            s, *origins = place_two_up(w, h, sw, sh, inset)
            x, y = origins[origin_idx - 1]
            if marks and bleed_mm is not None:
                ops += [
                    f"{a:.3f} {b:.3f} m {c:.3f} {d:.3f} l S"
                    for a, b, c, d in crop_mark_segments(
                        x, y, w * s, h * s, bleed_mm * MM_PT, MARK_LEN_MM * MM_PT
                    )
                ]
            ctm = Transformation().translate(-float(src.mediabox.left), -float(src.mediabox.bottom))
            sheet.merge_transformed_page(src, ctm.scale(s).translate(x, y))
        if ops:
            _draw(writer, sheet, f"q {MARK_WIDTH_PT} w 0 G {' '.join(ops)} Q")
            ops = []
    return writer


def _draw(writer: PdfWriter, sheet, content: str) -> None:
    """Append a content stream (PDF operators) on top of ``sheet``."""
    from pypdf import PageObject
    from pypdf.generic import DecodedStreamObject, NameObject

    stream = DecodedStreamObject()
    stream.set_data(content.encode("ascii"))
    top = PageObject.create_blank_page(width=sheet.mediabox.width, height=sheet.mediabox.height)
    top[NameObject("/Contents")] = writer._add_object(stream)
    sheet.merge_page(top)


def sheet_for(name: str) -> tuple[float, float] | None:
    """Sheet size (mm) for a ``sheet_size`` setting; ``auto`` gives None (chosen per document)."""
    return None if name == "auto" else SHEETS[name]


def spread_sides(n: int) -> list[tuple[int | None, int | None]]:
    """Reader spreads of ``n`` pages in reading order: page 1 alone on the right, then pairs."""
    pages: list[int | None] = [None, *range(1, n + 1)]
    if len(pages) % 2:
        pages.append(None)
    return [(pages[i], pages[i + 1]) for i in range(0, len(pages), 2)]


def impose_spreads(
    pdf: bytes,
    sheet_mm: tuple[float, float] | None = None,
    bleed_mm: float | None = None,
) -> bytes:
    """Lay a finished PDF out as 2-up reader spreads (``spread_sides``), one landscape sheet each."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf))
    writer = impose_pages(
        reader, spread_sides(len(reader.pages)), sheet_mm=sheet_mm, bleed_mm=bleed_mm
    )
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def impose_booklets(
    pdf: bytes,
    booklet_of: Sequence[int | None],
    bleed_mm: float | None = None,
    sheet_mm: tuple[float, float] | None = None,
) -> bytes:
    """Impose a finished PDF; ``booklet_of[i]`` is the booklet index of page ``i`` (None = not in one).

    Each booklet (pages contiguous, padded with blanks to a multiple of 4) becomes its sheet sides
    in ``imposition_order``. Pages outside any booklet (separate covers) are kept as they are,
    at their place relative to the booklets (before the first / after the last).
    ``bleed_mm`` not None adds crop marks to the imposed sheets (see ``impose_pages``).
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
        impose_pages(reader, sides, sheet_mm=sheet_mm, writer=out, bleed_mm=bleed_mm)
    for n in (n for n in plain if n > first):
        out.add_page(reader.pages[n - 1])
    buf = io.BytesIO()
    out.write(buf)
    return buf.getvalue()
