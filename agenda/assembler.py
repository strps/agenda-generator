"""Final page order, padding and booklets: the page plan data types."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from agenda.grid import Side, side_for_page
from agenda.pages.base import BasePage

Kind = Literal["page", "filler", "padding"]


@dataclass(frozen=True, eq=False)
class PlanEntry:
    """One physical page of the final agenda.

    A 2-page spread is two entries sharing the same ``ctx`` object, with
    ``page_in_instance`` 0 and 1; the drawer calls ``draw`` once, on the entry
    with ``page_in_instance == 0``. Blank fillers (``starts_on``) and padding
    use ``kind`` "filler"/"padding"; ``page_class`` is None for a blank
    filler and a real class (e.g. Notes) for padding that draws something.
    """

    page_class: type[BasePage] | None
    ctx: dict[str, Any]
    page_number: int  # 1-based
    side: Side  # always from grid.side_for_page(page_number)
    booklet_index: int | None  # 1-based; None only for hand-built entries
    section: str
    page_in_instance: int = 0
    kind: Kind = "page"

    @property
    def is_blank(self) -> bool:
        return self.page_class is None

    @property
    def starts_instance(self) -> bool:
        """True when the drawer must call ``draw`` for this entry."""
        return self.page_in_instance == 0 and self.page_class is not None


def make_entry(
    page_class: type[BasePage] | None,
    ctx: dict[str, Any],
    page_number: int,
    section: str,
    *,
    booklet_index: int | None = None,
    page_in_instance: int = 0,
    kind: Kind = "page",
) -> PlanEntry:
    """Build an entry, deriving ``side`` from ``grid.side_for_page``."""
    return PlanEntry(
        page_class, ctx, page_number, side_for_page(page_number),
        booklet_index, section, page_in_instance, kind,
    )  # fmt: skip


@dataclass(frozen=True)
class PagePlan:
    """Ordered, immutable list of entries; entry ``i`` has ``page_number == i + 1``."""

    entries: tuple[PlanEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        for i, e in enumerate(self.entries, start=1):
            if e.page_number != i:
                raise ValueError(f"entry {i} has page_number {e.page_number}")
            if e.side != side_for_page(i):
                raise ValueError(f"page {i} has side {e.side!r}")

    @classmethod
    def from_entries(cls, entries: Sequence[PlanEntry]) -> PagePlan:
        return cls(tuple(entries))

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[PlanEntry]:
        return iter(self.entries)

    def __getitem__(self, i: int) -> PlanEntry:
        return self.entries[i]

    @property
    def page_count(self) -> int:
        return len(self.entries)

    def by_section(self, section: str) -> list[PlanEntry]:
        return [e for e in self.entries if e.section == section]

    def by_booklet(self, index: int) -> list[PlanEntry]:
        return [e for e in self.entries if e.booklet_index == index]

    def drawn(self) -> list[PlanEntry]:
        """Entries the drawer must call ``draw`` for (once per instance)."""
        return [e for e in self.entries if e.starts_instance]

    def sections(self) -> list[tuple[str, int, int]]:
        """Consecutive runs as ``(section, first_page, last_page)``, for the section bar."""
        runs: list[tuple[str, int, int]] = []
        for e in self.entries:
            if runs and runs[-1][0] == e.section:
                runs[-1] = (e.section, runs[-1][1], e.page_number)
            else:
                runs.append((e.section, e.page_number, e.page_number))
        return runs


def pages_per_sheet(folded: bool = True) -> int:
    """Pages on one physical sheet: 4 folded (saddle stitch), 2 flat (double-sided)."""
    return 4 if folded else 2


def pages_per_booklet(size: int, unit: str = "sheets", folded: bool = True) -> int:
    """Pages in one booklet. ``unit="pages"`` returns ``size`` as is (even if not a multiple
    of 4 when folded; that is rejected by validation, not here)."""
    return size * pages_per_sheet(folded) if unit == "sheets" else size


@dataclass(frozen=True)
class BookletLayout:
    """Result of ``plan_booklets``: ``count`` booklets of ``pages_per_booklet`` pages.

    ``padding`` = blank pages needed to fill the last booklet (0 if exact fit);
    ``overflow`` = pages that don't fit when a fixed ``num_booklets`` is too small.
    """

    total_pages: int
    pages_per_booklet: int
    count: int
    padding: int
    overflow: int = 0


def booklet_index_for(page_number: int, pages_per_booklet: int) -> int:
    """1-based booklet holding ``page_number`` (1-based)."""
    return (page_number - 1) // pages_per_booklet + 1


def plan_booklets(
    total_pages: int, pages_per_booklet: int, num_booklets: int | str = "auto"
) -> BookletLayout:
    """Booklet count and padding for ``total_pages`` (>= 0).

    ``"auto"``: ``ceil(total / per_booklet)`` booklets (at least 1). An int fixes the count;
    padding is then ``n * per_booklet - total``, or 0 with ``overflow`` > 0 when the pages
    don't fit (no truncation; the caller/validation decides). Fillers count as pages.
    """
    if pages_per_booklet < 1:
        raise ValueError("pages_per_booklet must be >= 1")
    n = (
        max(1, math.ceil(total_pages / pages_per_booklet))
        if num_booklets == "auto"
        else int(num_booklets)
    )
    capacity = n * pages_per_booklet
    return BookletLayout(
        total_pages,
        pages_per_booklet,
        n,
        max(0, capacity - total_pages),
        max(0, total_pages - capacity),
    )


def _extras(config: Any, category: str) -> list[type[BasePage]]:
    """Optional/value-added classes enabled by ``config.pages`` (ids), in catalog order."""
    from agenda.catalog import pages_by_category

    if config.pages is None:
        return []
    return [c for c in pages_by_category(category) if c.id in config.pages]


def build_plan(config: Any) -> PagePlan:
    """Ordered ``PagePlan`` for ``config`` (page numbers 1..N, 1-based ``booklet_index``).

    Order: front matter (cover, personal info, yearly) -> per month: monthly, then per owned
    week its weekly spread and that week's dailies (dates inside ``config.year`` and in ``config.daily_months``) -> optional ->
    value-added -> back matter (notes, contacts, padding, back cover). With
    ``config.separate_covers`` the cover is page 1 followed by a blank inside-cover filler, and a
    blank inside-back filler precedes the back cover; those 4 pages have ``booklet_index`` None and
    padding/booklets are computed on the inner block (pages 3..N-2, which starts on a right page). A multi-page instance is
    ``cls.pages`` entries sharing one ctx. One blank filler (``kind="filler"``, section of the
    page it precedes) is inserted before an instance whose ``starts_on`` side doesn't match.
    """
    from agenda.calendar import weeks_by_month
    from agenda.catalog import get_page
    from agenda.pages.core import (
        BackCover,
        Contacts,
        Cover,
        Daily,
        Monthly,
        Notes,
        PersonalInfo,
        Weekly,
        Yearly,
    )

    entries: list[PlanEntry] = []

    def put(cls: type[BasePage], ctx: dict[str, Any], kind: Kind = "page") -> None:
        want = cls.starts_on
        if want != "any" and side_for_page(len(entries) + 1) != want:
            entries.append(make_entry(None, {}, len(entries) + 1, cls.section, kind="filler"))
        for k in range(cls.pages):
            entries.append(
                make_entry(cls, ctx, len(entries) + 1, cls.section, page_in_instance=k, kind=kind)
            )

    sep = bool(config.separate_covers)
    lead = 0  # pages before the inner block (not in any booklet)
    for cls in (Cover, PersonalInfo, Yearly):
        put(cls, {})
        if sep and cls is Cover:
            # Blank inside-cover page so the inner block starts on a right page.
            entries.append(make_entry(None, {}, len(entries) + 1, Cover.section, kind="filler"))
            lead = len(entries)
    weekly_ctx = {(c["iso_year"], c["number"]): c for c in Weekly().instances(config)}
    daily_ctx = {c["date"]: c for c in Daily().instances(config)}
    for month, weeks in weeks_by_month(config.year, config.week_start).items():
        put(Monthly, {"month": month})
        for week in weeks:
            if "weekly" in config.planners:
                put(Weekly, weekly_ctx[(week.iso_year, week.number)])
            if "daily" in config.planners:
                for d in week.days:
                    if d in daily_ctx and d.month in config.daily_months:
                        put(Daily, daily_ctx[d])
    for category in ("optional", "value_added"):
        for cls in _extras(config, category):
            for ctx in cls().instances(config):
                put(cls, ctx)
    for cls in (Notes, Contacts):
        put(cls, {})
    per = pages_per_booklet(config.booklet_size, config.booklet_unit, config.booklet_folded)
    base = list(entries)
    pad_cls = get_page(config.pad_with)
    pad_ctxs = pad_cls().instances(config) or [{}]

    def try_padding(units: int, blank: bool) -> int:
        """Rebuild the tail with ``units`` padding units + back cover; return total pages."""
        entries[:] = base
        for u in range(units):
            if blank:
                entries.append(make_entry(None, {}, len(entries) + 1, "front_back", kind="padding"))
            else:
                put(pad_cls, dict(pad_ctxs[u % len(pad_ctxs)]), kind="padding")
        inner = len(entries) - lead  # pages counted in booklets
        if sep:  # inside back cover (blank), then the cover; neither is in a booklet
            entries.append(make_entry(None, {}, len(entries) + 1, BackCover.section, kind="filler"))
            put(BackCover, {})
            return inner
        put(BackCover, {})
        return len(entries)

    # Padding goes BEFORE the back cover so the cover stays the last page. The count comes from
    # plan_booklets on the total (back matter included); searching unit by unit keeps it exact
    # when the pad class is a multi-page spread or the back cover needs a starts_on filler.
    # If no whole number of pad units fits exactly, fall back to blank pages (page_class=None).
    nb = config.num_booklets
    limit = 2 * per + 4 if nb == "auto" else int(nb) * per + 4
    done = False
    for blank in (False, True):
        for units in range(limit):
            total = try_padding(units, blank)
            lay = plan_booklets(total, per, nb)
            if lay.padding == 0 and lay.overflow == 0:
                done = True
                break
            if units == 0 and lay.overflow > 0:
                done = True  # too many pages for a fixed num_booklets: no padding (summary warns)
                break
        if done:
            break
    if not done:
        try_padding(0, False)
    inner_end = len(entries) - 2 if sep else len(entries)  # last inner page number

    def index(e: PlanEntry) -> int | None:
        if sep and not lead < e.page_number <= inner_end:
            return None
        return booklet_index_for(e.page_number - lead, per)

    return PagePlan(tuple(replace(e, booklet_index=index(e)) for e in entries))
