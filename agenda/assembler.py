"""Final page order, padding and booklets: the page plan data types."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
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
    booklet_index: int | None  # None until the booklet task assigns it (1-based after)
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
