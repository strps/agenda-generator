"""Qt-free legend entries and summary-line text for the bottom strip."""

from collections import Counter
from collections.abc import Sequence
from typing import NamedTuple

from agenda.gui.bar_model import SECTION_LABELS, page_keys

NO_PLAN_TEXT = "No agenda: fix the settings"


class LegendEntry(NamedTuple):
    key: str
    label: str
    count: int


def legend_entries(plan: Sequence) -> list[LegendEntry]:
    """One entry per section present in ``plan``, in SECTION_LABELS order, with page counts."""
    counts = Counter(page_keys(plan))
    known = [LegendEntry(k, v, counts[k]) for k, v in SECTION_LABELS.items() if counts[k]]
    extra = [LegendEntry(k, k, n) for k, n in counts.items() if k not in SECTION_LABELS]
    return known + extra


def _n(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def summary_text(summary) -> str:
    """'498 pages · 125 sheets · 25 booklets · 2 padding pages' from an assembler PlanSummary.
    Padding is omitted when 0; warnings are appended as a count (see ``summary_tooltip``)."""
    parts = [
        _n(summary.total_pages, "page"),
        _n(summary.total_sheets, "sheet"),
        _n(summary.booklets, "booklet"),
    ]
    if summary.padding_pages:
        parts.append(_n(summary.padding_pages, "padding page"))
    if summary.warnings:
        parts.append("⚠ " + _n(len(summary.warnings), "warning"))
    return " · ".join(parts)


def summary_tooltip(summary) -> str:
    """Full warning texts, one per line ('' when none)."""
    return "\n".join(summary.warnings)
