"""Section bar geometry (Qt-free): proportional segments, gaps, padding runs, ticks, marker."""

from collections.abc import Sequence
from dataclasses import dataclass

GAP_PX = 2.0
PADDING = "padding"  # pseudo-section key for auto-inserted filler pages


@dataclass(frozen=True)
class Segment:
    section: str  # a plan section, or PADDING
    first: int  # 0-based plan index of the first page
    count: int
    x: float
    width: float

    @property
    def padding(self) -> bool:
        return self.section == PADDING


def page_keys(plan: Sequence) -> list[str]:
    """Per-page segment key: PADDING for padding pages, else the entry's section."""
    return [PADDING if e.kind == "padding" else e.section for e in plan]


def booklet_starts(booklet_of: Sequence[int | None]) -> list[int]:
    """0-based index of the first page of each booklet, in order."""
    starts, prev = [], None
    for i, b in enumerate(booklet_of):
        if b is not None and b != prev:
            starts.append(i)
        prev = b
    return starts


@dataclass(frozen=True)
class BarGeometry:
    """Layout of the bar for `total` pages in `width` px; consecutive same-key pages merge."""

    keys: tuple[str, ...]
    booklets: tuple[int, ...]  # 0-based first page of each booklet
    width: float
    gap: float = GAP_PX

    @property
    def total(self) -> int:
        return len(self.keys)

    @property
    def runs(self) -> list[tuple[str, int, int]]:
        out: list[tuple[str, int, int]] = []
        for i, k in enumerate(self.keys):
            if out and out[-1][0] == k:
                out[-1] = (k, out[-1][1], out[-1][2] + 1)
            else:
                out.append((k, i, 1))
        return out

    @property
    def page_width(self) -> float:
        if not self.keys:
            return 0.0
        gaps = (len(self.runs) - 1) * self.gap
        return max(self.width - gaps, 0.0) / len(self.keys)

    def segments(self) -> list[Segment]:
        pw = self.page_width
        out = []
        for n, (k, first, count) in enumerate(self.runs):
            out.append(Segment(k, first, count, first * pw + n * self.gap, count * pw))
        return out

    def ticks(self) -> list[float]:
        """x of each booklet's first page (its left edge)."""
        return [self.segment_x(i) for i in self.booklets]

    def segment_x(self, index: int) -> float:
        for s in self.segments():
            if s.first <= index < s.first + s.count:
                return s.x + (index - s.first) * self.page_width
        return self.width

    def marker_x(self, index: int) -> float:
        """Horizontal centre of page `index` (clamped)."""
        if not self.keys:
            return 0.0
        index = min(max(index, 0), self.total - 1)
        return self.segment_x(index) + self.page_width / 2


def geometry(plan: Sequence, width: float, gap: float = GAP_PX) -> BarGeometry:
    keys = tuple(page_keys(plan))
    return BarGeometry(keys, tuple(booklet_starts([e.booklet_index for e in plan])), width, gap)
