"""Qt-free data layer for the day-page extras: user holidays, dated notes and daily phrases.

The files are CSV (``.csv``), so any spreadsheet can make them; a header row is optional.
Dated files (holidays, notes) have the columns ``month, day, text`` and an optional ``year``
(empty = every year). Phrase files have one phrase per row in the first column. The delimiter
(``,``, ``;`` or tab) is detected; UTF-8 (with or without BOM) is read, else Windows-1252.
Empty rows and rows whose first cell starts with ``#`` are ignored.

Any other extension is the legacy text format: one entry per line, ``#`` comments, dated lines
``MM-DD text`` / ``YYYY-MM-DD text``. Imports no ``Config`` (its validators import this lazily).
"""

from __future__ import annotations

import csv
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


def is_csv(path: Path | str) -> bool:
    return Path(path).suffix.lower() == ".csv"


def read_rows(path: Path | str) -> list[tuple[int, list[str]]]:
    """(1-based row number, stripped cells) of a CSV file, skipping empty and ``#`` rows."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # spreadsheet "CSV" on Windows
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    delim = max(",;\t", key=first.count) if first else ","
    out = []
    for number, row in enumerate(csv.reader(text.splitlines(), delimiter=delim), start=1):
        cells = [c.strip() for c in row]
        while cells and not cells[-1]:
            cells.pop()
        if cells and not cells[0].startswith("#"):
            out.append((number, cells))
    return out


_PHRASE_HEADERS = {"phrase", "phrases", "frase", "frases", "text", "texto", "quote", "quotes"}


def load_phrases(path: Path | str) -> list[str]:
    """Phrases of a file: first CSV column (a header such as ``phrase`` is skipped), or lines."""
    if not is_csv(path):
        return read_lines(path)
    rows = read_rows(path)
    if rows and rows[0][1][0].lower() in _PHRASE_HEADERS:
        rows = rows[1:]
    return [cells[0] for _, cells in rows if cells[0]]


def _int_cell(cells: list[str], i: int) -> int | None:
    """Integer in cell ``i`` (``"3"``, ``"03"``, ``"3.0"``), None when empty or missing."""
    if i >= len(cells) or not cells[i]:
        return None
    return int(float(cells[i]))


def parse_dated_rows(rows: list[tuple[int, list[str]]], year: int) -> dict[date, str]:
    """``month, day, text[, year]`` rows -> {date in ``year``: text}; a non-numeric first row is
    a header. Same joining and Feb 29 rule as ``parse_dated``; ValueError names the bad row."""
    out: dict[date, str] = {}
    for index, (number, cells) in enumerate(rows):
        try:
            month, day, y = _int_cell(cells, 0), _int_cell(cells, 1), _int_cell(cells, 3)
        except ValueError:
            if index == 0:
                continue  # header row
            raise ValueError(
                f"row {number}: month, day and year must be numbers: {cells}"
            ) from None
        text = cells[2] if len(cells) > 2 else ""
        if month is None or day is None or not text:
            raise ValueError(f"row {number}: expected month, day, text (year optional): {cells}")
        try:
            d = date(y if y is not None else year, month, day)
        except ValueError:
            if y is None and (month, day) == (2, 29):
                continue
            raise ValueError(f"row {number}: invalid date {month}/{day}: {cells}") from None
        if d.year != year:
            continue
        out[d] = f"{out[d]}{JOIN}{text}" if d in out else text
    return out


def load_dated(path: Path | str, year: int) -> dict[date, str]:
    """Entries of a dated file (CSV or legacy text) for ``year``."""
    if is_csv(path):
        return parse_dated_rows(read_rows(path), year)
    return parse_dated(read_lines(path), year)


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
