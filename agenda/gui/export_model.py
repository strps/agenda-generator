"""Qt-free export helpers: default destination and progress fraction."""

from __future__ import annotations

from pathlib import Path

from agenda.config import Config


def default_path(cfg: Config) -> str:
    """Suggested destination for the save dialog: ``cfg.output`` (a .pdf suffix is ensured)."""
    return str(ensure_pdf(cfg.output))


def ensure_pdf(path: str | Path) -> Path:
    p = Path(path)
    return p if p.suffix.lower() == ".pdf" else p.with_suffix(p.suffix + ".pdf")


def progress_fraction(done: int, total: int) -> float:
    """``done / total`` clamped to 0..1; 0 when total is not positive."""
    if total <= 0:
        return 0.0
    return min(max(done / total, 0.0), 1.0)


def progress_percent(done: int, total: int) -> int:
    return round(progress_fraction(done, total) * 100)
