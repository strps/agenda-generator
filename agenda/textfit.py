"""Qt-free and fpdf-free text fitting for page header/footer bands, plus a log of cut texts.

``width_of(text)`` measures ``text`` at ``size_pt`` (widths scale linearly with the font size);
``line_height_of(size)`` gives one line's height at a size. Units only need to match ``width``
and ``height``. Region ids are stable strings ("header", "footer"); UI text is built elsewhere.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .day_extras import truncate

FIT_MODES = ("overflow", "ellipsis", "shrink", "wrap")
FOOTER_FIT_MODES = ("ellipsis", "shrink", "wrap")

_STEP_PT = 0.25
_EPS = 1e-9


@dataclass(frozen=True)
class FitResult:
    lines: tuple[str, ...]
    size_pt: float
    cut: bool


def _sizes(size_pt: float, min_scale: float):
    """Candidate sizes from ``size_pt`` down to ``size_pt * min_scale`` (inclusive)."""
    low = size_pt * min_scale
    s = size_pt
    while s > low + _EPS:
        yield s
        s -= _STEP_PT
    yield low


def _scaled(width_of: Callable[[str], float], size_pt: float, size: float):
    k = size / size_pt if size_pt else 1.0
    return lambda s: width_of(s) * k


def _wrap_lines(text: str, width: float, n: int, wf) -> tuple[list[str], bool]:
    lines: list[str] = []
    rest = text.strip()
    while rest and len(lines) < n:
        if len(lines) == n - 1:  # last line: whatever is left, shortened if needed
            cut = wf(rest) > width + _EPS
            lines.append(truncate(rest, width + _EPS, wf))
            return lines, cut
        if wf(rest) <= width + _EPS:
            lines.append(rest)
            return lines, False
        words = rest.split(" ")
        take = ""
        for i in range(len(words)):
            cand = " ".join(words[: i + 1])
            if wf(cand) > width + _EPS:
                break
            take = cand
        if not take:  # one word wider than the line: break it by characters
            k = 1
            while k < len(rest) and wf(rest[: k + 1]) <= width + _EPS:
                k += 1
            take = rest[:k]
        lines.append(take)
        rest = rest[len(take) :].lstrip()
    return lines, False


def fit_text(
    text: str,
    width: float,
    height: float,
    size_pt: float,
    mode: str,
    width_of: Callable[[str], float],
    line_height_of: Callable[[float], float],
    min_scale: float = 0.6,
    max_lines: int = 2,
) -> FitResult:
    """Fit ``text`` into ``width`` x ``height`` according to ``mode`` (see ``FIT_MODES``)."""
    if mode not in FIT_MODES:
        raise ValueError(f"unknown fit mode {mode!r}")
    if mode == "overflow" or width_of(text) <= width:
        return FitResult((text,), size_pt, False)
    if mode == "ellipsis":
        return FitResult((truncate(text, width, width_of),), size_pt, True)
    if mode == "shrink":
        last = size_pt
        for s in _sizes(size_pt, min_scale):
            last = s
            if _scaled(width_of, size_pt, s)(text) <= width:
                return FitResult((text,), s, False)
        return FitResult((truncate(text, width, _scaled(width_of, size_pt, last)),), last, True)
    # wrap
    size = size_pt * min_scale
    for s in _sizes(size_pt, min_scale):
        if line_height_of(s) * max_lines <= height + _EPS:
            size = s
            break
    n = max(1, min(max_lines, int((height + _EPS) // max(line_height_of(size), _EPS))))
    lines, cut = _wrap_lines(text, width, n, _scaled(width_of, size_pt, size))
    return FitResult(tuple(lines), size, cut)


@dataclass(frozen=True)
class CutEntry:
    page: int
    region: str
    text: str


class CutLog:
    """Collects texts that were shortened, with their agenda page and region."""

    def __init__(self) -> None:
        self._entries: list[CutEntry] = []

    def add(self, page: int, region: str, text: str) -> None:
        self._entries.append(CutEntry(page, region, text))

    @property
    def entries(self) -> list[CutEntry]:
        return sorted(self._entries, key=lambda e: e.page)  # stable: keeps insertion order

    def pages(self, region: str | None = None) -> list[int]:
        return sorted({e.page for e in self._entries if region is None or e.region == region})

    def __bool__(self) -> bool:
        return bool(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


def format_ranges(pages) -> str:
    """``[1, 3, 4, 5]`` -> ``"1, 3-5"`` (sorted, duplicates dropped)."""
    out: list[str] = []
    run: list[int] = []

    def flush() -> None:
        if run:
            out.append(str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}")

    for p in sorted(set(pages)):
        if run and p == run[-1] + 1:
            run.append(p)
        else:
            flush()
            run = [p]
    flush()
    return ", ".join(out)
