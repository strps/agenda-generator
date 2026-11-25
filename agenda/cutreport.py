"""Qt-free text for the cut log: which header/footer texts were shortened, on which pages."""

from __future__ import annotations

from agenda.textfit import CutLog, format_ranges
from agenda.uitext import tr

REGIONS = ("header", "footer")
MAX_TEXT = 60


def _plural(key: str, n: int, **fmt: object) -> str:
    return tr(f"{key}.{'one' if n == 1 else 'other'}", n=n, **fmt)


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


def cut_report_lines(log: CutLog) -> list[str]:
    """One summary line per region, each followed by one line per distinct cut text."""
    lines: list[str] = []
    regions = [r for r in REGIONS if log.pages(r)]
    regions += sorted({e.region for e in log.entries} - set(REGIONS))
    for region in regions:
        pages = log.pages(region)
        key = f"cuts.{region}" if region in REGIONS else "cuts.other"
        lines.append(_plural(key, len(pages), pages=format_ranges(pages)))
        by_text: dict[str, set[int]] = {}
        for e in log.entries:
            if e.region == region:
                by_text.setdefault(_short(e.text), set()).add(e.page)
        for text, tpages in by_text.items():
            ordered = sorted(tpages)
            lines.append(
                _plural("cuts.item", len(ordered), text=text, pages=format_ranges(ordered))
            )
    return lines


def cut_status(log: CutLog) -> str:
    """Short one-line suffix for status bars: how many agenda pages have shortened text."""
    n = len(log.pages())
    return _plural("cuts.status", n) if n else ""
