"""Qt-free data layer for the day-page extras: user holidays, dated notes and daily phrases.

File format (UTF-8): one entry per line, blank lines and lines starting with ``#`` are ignored.
Dated lines are ``MM-DD text`` (every year) or ``YYYY-MM-DD text`` (that year only); the date and
the text are separated by whitespace, ``;`` or a tab. Imports no ``Config`` (its validators import
this module lazily).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

JOIN = " · "
_LINE = re.compile(r"^(?:(\d{4})-)?(\d{2})-(\d{2})[\s;]+(\S.*)$")


def read_lines(path: Path | str) -> list[str]:
    """Stripped, non-blank, non-comment lines of a UTF-8 file. ValueError names the path."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from None
    lines = (ln.strip() for ln in text.splitlines())
    return [ln for ln in lines if ln and not ln.startswith("#")]


def parse_dated(lines: list[str], year: int) -> dict[date, str]:
    """``MM-DD text`` / ``YYYY-MM-DD text`` lines -> {date in ``year``: text}.

    Entries on one date are joined with `` · ``. A bad line raises ValueError with its 1-based
    number. ``MM-DD`` of Feb 29 is skipped in non-leap years.
    """
    out: dict[date, str] = {}
    for number, line in enumerate(lines, start=1):
        m = _LINE.match(line.strip())
        if m is None:
            raise ValueError(f"line {number}: expected 'MM-DD text' or 'YYYY-MM-DD text': {line!r}")
        y, month, day, text = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        try:
            d = date(int(y) if y else year, month, day)
        except ValueError:
            if y is None and (month, day) == (2, 29):
                continue
            raise ValueError(f"line {number}: invalid date in {line!r}") from None
        if d.year != year:
            continue
        out[d] = f"{out[d]}{JOIN}{text}" if d in out else text
    return out


def builtin_quotes(language: str) -> list[str]:
    """The twelve built-in phrases (i18n ``quotes.1`` .. ``quotes.12``)."""
    from agenda.i18n import t

    return [t(f"quotes.{i}", language) for i in range(1, 13)]


def quote_for(d: date, quotes: list[str]) -> str | None:
    """Phrase for a date: one per day of the year, cycling. None for an empty list."""
    if not quotes:
        return None
    return quotes[(d.timetuple().tm_yday - 1) % len(quotes)]


def truncate(text: str, max_width: float, width_of) -> str:
    """``text`` if ``width_of(text) <= max_width``, else the longest prefix + "…" that fits."""
    if width_of(text) <= max_width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:  # longest prefix whose width with "…" fits
        mid = (lo + hi + 1) // 2
        if width_of(text[:mid].rstrip() + "…") <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + "…"
