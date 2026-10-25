"""Qt-free preview logic: which plan pages each mode shows, navigation and zoom math.

All page indices are 0-based plan indices (page number - 1). Page 1 is a right page, so spreads
are (2,3), (4,5), ...; page 1 and an even last page stand alone.
"""

from collections.abc import Sequence

SINGLE, SPREAD, SHEET = "single", "spread", "sheet"
MODES = (SINGLE, SPREAD, SHEET)
FIT = "fit"
ZOOM_CHOICES = (FIT, 50, 75, 100, 150, 200)
PX_PER_PT = 96 / 72  # 100% = actual size at 96 dpi
_FIT_GAP_PX = 8


def effective_mode(mode: str, folded: bool) -> str:
    """Sheet mode needs folded booklets; otherwise it falls back to spread."""
    if mode not in MODES:
        raise ValueError(f"unknown preview mode {mode!r}")
    return SPREAD if mode == SHEET and not folded else mode


def spread_indices(index: int, total: int) -> list[int]:
    """Left-to-right pages of the spread containing ``index``."""
    _check(index, total)
    start = index if index % 2 == 1 else index - 1  # index odd = even page number = left page
    return [i for i in (start, start + 1) if 0 <= i < total]


def sheet_rows(index: int, booklet_of: Sequence[int | None]) -> list[list[int]]:
    """Rows [front side, back side] (left-to-right) of the folded sheet holding ``index``.

    ``booklet_of[i]`` is the booklet number of plan entry i (None = outside booklets, e.g. a
    separate cover). Pages of a booklet are numbered 1..N in plan order; sheet s (1-based) has
    front (N-2s+2, 2s-1) and back (2s, N-2s+1). A page outside any booklet is shown as a spread.
    """
    total = len(booklet_of)
    _check(index, total)
    b = booklet_of[index]
    if b is None:
        return [spread_indices(index, total)]
    members = [i for i, x in enumerate(booklet_of) if x == b]
    n = len(members)
    k = members.index(index) + 1
    s = (k + 1) // 2 if k <= n // 2 else (n - k) // 2 + 1
    front = (n - 2 * s + 2, 2 * s - 1)
    back = (2 * s, n - 2 * s + 1)
    return [[members[p - 1] for p in side if 1 <= p <= n] for side in (front, back)]


def sheet_number(index: int, booklet_of: Sequence[int | None]) -> int | None:
    """1-based sheet of ``index`` within its booklet (None outside booklets)."""
    b = booklet_of[index]
    if b is None:
        return None
    members = [i for i, x in enumerate(booklet_of) if x == b]
    n, k = len(members), members.index(index) + 1
    return (k + 1) // 2 if k <= n // 2 else (n - k) // 2 + 1


def display_rows(
    mode: str, index: int, total: int, booklet_of: Sequence[int | None], folded: bool
) -> list[list[int]]:
    """Rows of plan indices the preview shows for ``mode`` with ``index`` current."""
    mode = effective_mode(mode, folded)
    if mode == SINGLE:
        _check(index, total)
        return [[index]]
    if mode == SPREAD:
        return [spread_indices(index, total)]
    return sheet_rows(index, booklet_of)


def render_indices(rows: Sequence[Sequence[int]]) -> list[int]:
    """Sorted unique indices to pass to ``render_pages``."""
    return sorted({i for row in rows for i in row})


def pdf_position(rows: Sequence[Sequence[int]], index: int) -> int:
    """Position of plan ``index`` in the PDF that ``render_pages`` returns for ``rows``."""
    return render_indices(rows).index(index)


def step(
    mode: str, index: int, delta: int, total: int, booklet_of: Sequence[int | None], folded: bool
) -> int:
    """Index after moving ``delta`` units (pages, spreads or sheets), clamped to the plan."""
    mode = effective_mode(mode, folded)
    _check(index, total)
    if mode == SINGLE:
        return min(max(index + delta, 0), total - 1)
    anchors = _sheet_anchors(total, booklet_of) if mode == SHEET else None
    cur = index
    for _ in range(abs(delta)):
        if anchors is None:
            span = spread_indices(cur, total)
            nxt = max(span) + 1 if delta > 0 else min(span) - 1
        else:
            pos = anchors.index(min(i for row in sheet_rows(cur, booklet_of) for i in row))
            pos += 1 if delta > 0 else -1
            nxt = anchors[pos] if 0 <= pos < len(anchors) else -1
        if not 0 <= nxt < total:
            break
        cur = nxt
    return cur


def _sheet_anchors(total: int, booklet_of: Sequence[int | None]) -> list[int]:
    """Lowest plan index of every sheet (or stand-alone spread), in plan order."""
    anchors: list[int] = []
    seen: set[int] = set()
    for i in range(total):
        if i in seen:
            continue
        span = [j for row in sheet_rows(i, booklet_of) for j in row]
        seen.update(span)
        anchors.append(min(span))
    return anchors


def zoom_scale(
    zoom: str | int,
    page_pt: tuple[float, float],
    rows: int,
    cols: int,
    avail_px: tuple[float, float],
) -> float:
    """pdfium render scale (1.0 = 72 dpi). ``zoom`` is "fit" or a percent; fit shrinks or grows
    the ``cols`` x ``rows`` page grid to the available pixels."""
    if zoom == FIT:
        w, h = page_pt
        gap = _FIT_GAP_PX * (cols - 1), _FIT_GAP_PX * (rows - 1)
        sx = max(avail_px[0] - gap[0], 1) / (w * cols)
        sy = max(avail_px[1] - gap[1], 1) / (h * rows)
        return max(min(sx, sy), 0.05)
    if zoom not in ZOOM_CHOICES:
        raise ValueError(f"unknown zoom {zoom!r}")
    return PX_PER_PT * int(zoom) / 100


def label(rows: Sequence[Sequence[int]], total: int, mode: str) -> str:
    """Toolbar text, 1-based page numbers, e.g. "Spread 72-73 of 498"."""
    name = {SINGLE: "Page", SPREAD: "Spread", SHEET: "Sheet"}[mode]
    pages = sorted(i + 1 for i in render_indices(rows))
    if mode == SHEET:
        span = ",".join(map(str, pages))
    else:
        span = str(pages[0]) if len(pages) == 1 else f"{pages[0]}-{pages[-1]}"
    return f"{name} {span} of {total}"


def _check(index: int, total: int) -> None:
    if not 0 <= index < total:
        raise IndexError(f"page index {index} out of range (0..{total - 1})")
