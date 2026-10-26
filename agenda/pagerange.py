"""Page range parsing for partial exports (Qt-free, no Config import)."""

from __future__ import annotations

from collections.abc import Iterable


def parse_page_range(text: str | None, total: int) -> list[int] | None:
    """Parse ``"1-3, 5"`` into sorted, unique 1-based pages; empty/"all"/None -> None (all pages).

    Raises ValueError naming the bad token.
    """
    if text is None or text.strip() == "" or text.strip().lower() == "all":
        return None
    pages: set[int] = set()
    for raw in text.split(","):
        token = raw.strip()
        lo_s, sep, hi_s = token.partition("-")
        try:
            lo = int(lo_s.strip())
            hi = int(hi_s.strip()) if sep else lo
        except ValueError:
            raise ValueError(f"bad page range '{token}': use numbers like 1-4,9") from None
        if lo < 1 or hi < 1:
            raise ValueError(f"bad page range '{token}': pages start at 1")
        if hi < lo:
            raise ValueError(f"bad page range '{token}': {hi} is before {lo}")
        if hi > total:
            raise ValueError(f"bad page range '{token}': the agenda has only {total} pages")
        pages.update(range(lo, hi + 1))
    return sorted(pages)


def format_page_range(pages: Iterable[int]) -> str:
    """Compress pages into runs: [1,2,3,5] -> "1-3,5"."""
    out: list[str] = []
    run: list[int] = []
    for p in sorted(set(pages)):
        if run and p == run[-1] + 1:
            run.append(p)
            continue
        if run:
            out.append(_run(run))
        run = [p]
    if run:
        out.append(_run(run))
    return ",".join(out)


def _run(run: list[int]) -> str:
    return str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}"
