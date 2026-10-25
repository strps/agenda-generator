"""PDF writing (fpdf2), bookmarks and internal links."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from agenda import __version__
from agenda.config import Config

DEFAULT_OUTPUT = Path("output") / "agenda.pdf"


def new_document(cfg: Config) -> FPDF:
    """Create an empty FPDF in mm sized from `cfg.page_dimensions`, no auto page breaks."""
    pdf = FPDF(unit="mm", format=tuple(cfg.page_dimensions))
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.set_title(f"Agenda {cfg.year}")
    pdf.set_creator(f"agenda-gen {__version__}")
    pdf.set_author("agenda-gen")
    return pdf


def add_blank_pages(pdf: FPDF, n: int) -> FPDF:
    for _ in range(n):
        pdf.add_page()
    return pdf


def write_pdf(pdf: FPDF, path: str | Path = DEFAULT_OUTPUT) -> Path:
    """Write the document, creating parent directories."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def export_blank(cfg: Config, pages: int = 1, path: str | Path = DEFAULT_OUTPUT) -> Path:
    return write_pdf(add_blank_pages(new_document(cfg), pages), path)
