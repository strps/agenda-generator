"""Section bar geometry (Qt-free): proportional segments, gaps, padding runs, ticks, marker."""

from collections.abc import Sequence
from dataclasses import dataclass

from agenda.gui.preview_model import SPREAD, sheet_number, step

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

    def page_at(self, x: float) -> int | None:
        """Page under bar-x ``x``. Out of range clamps to the ends; a gap goes to the nearer side."""
        if not self.keys:
            return None
        segs = self.segments()
        if x <= segs[0].x:
            return 0
        pw = self.page_width
        for n, s in enumerate(segs):
            if x < s.x + s.width:
                return s.first + min(int((x - s.x) / pw), s.count - 1) if pw else s.first
            nxt = segs[n + 1] if n + 1 < len(segs) else None
            if nxt and x < nxt.x:
                return s.first + s.count - 1 if x - (s.x + s.width) < nxt.x - x else nxt.first
        return self.total - 1

    def marker_x(self, index: int) -> float:
        """Horizontal centre of page `index` (clamped)."""
        if not self.keys:
            return 0.0
        index = min(max(index, 0), self.total - 1)
        return self.segment_x(index) + self.page_width / 2


def geometry(plan: Sequence, width: float, gap: float = GAP_PX) -> BarGeometry:
    keys = tuple(page_keys(plan))
    return BarGeometry(keys, tuple(booklet_starts([e.booklet_index for e in plan])), width, gap)


SECTION_LABELS = {
    "front_back": "Front/back",
    "monthly": "Monthly",
    "weekly": "Weekly",
    "daily": "Daily",
    "optional": "Optional",
    "value_added": "Value-added",
    PADDING: "Padding",
}


def first_page_of(plan: Sequence, section: str) -> int | None:
    """0-based index of the first page of ``section`` (legend click); None if absent."""
    for i, k in enumerate(page_keys(plan)):
        if k == section:
            return i
    return None


def _day(d) -> str:
    return f"{d:%b} {d.day}"


def _detail(entry) -> str:
    ctx = entry.ctx or {}
    if entry.kind == "filler":
        return "Blank" if entry.is_blank else f"{entry.page_class.name} (filler)"
    if "days" in ctx:
        days = ctx["days"]
        a, b = days[0], days[-1]
        end = str(b.day) if a.month == b.month else _day(b)
        return f"Week {ctx['number']} ({_day(a)}\u2013{end})"
    if "date" in ctx:
        return f"{ctx['date']:%a} {_day(ctx['date'])}"
    if "month" in ctx and entry.section == "monthly":
        import calendar

        return calendar.month_name[ctx["month"]]
    cls = entry.page_class
    return getattr(cls, "name", "") if cls else ""


def tooltip_text(plan: Sequence, index: int) -> str:
    """e.g. `Page 143 \u00b7 Weekly \u00b7 Week 12 (Mar 16\u201322) \u00b7 Booklet 8, sheet 2`."""
    e = plan[index]
    key = PADDING if e.kind == "padding" else e.section
    parts = [f"Page {index + 1}", SECTION_LABELS.get(key, key)]
    if e.kind != "padding" and (d := _detail(e)):
        parts.append(d)
    if e.booklet_index is not None:
        sheet = sheet_number(index, [x.booklet_index for x in plan])
        parts.append(f"Booklet {e.booklet_index}, sheet {sheet}")
    return " \u00b7 ".join(parts)


def key_target(key: str, index: int, plan: Sequence) -> int:
    """Page to show after a navigation key: left/right = spread, pageup/pagedown = booklet,
    home/end = ends. Unknown keys and an empty plan keep ``index``."""
    total = len(plan)
    if not total:
        return index
    booklet_of = [e.booklet_index for e in plan]
    starts = booklet_starts(booklet_of)
    if key in ("left", "right"):
        return step(SPREAD, index, 1 if key == "right" else -1, total, booklet_of, False)
    if key == "home":
        return 0
    if key == "end":
        return total - 1
    if key == "pagedown":
        return next((s for s in starts if s > index), total - 1)
    if key == "pageup":
        return next((s for s in reversed(starts) if s < index), 0)
    return index
