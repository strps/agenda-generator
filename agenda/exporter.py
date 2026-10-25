"""PDF writing (fpdf2), bookmarks and internal links."""

from __future__ import annotations

import io
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from fpdf import FPDF

from agenda import __version__
from agenda.config import Config
from agenda.draw import draw_debug_grid
from agenda.grid import Grid

if TYPE_CHECKING:
    from agenda.assembler import PagePlan

DEFAULT_OUTPUT = Path("output") / "agenda.pdf"

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT_FAMILY = "Inter"
# fpdf2 style code -> file name. Use `pdf.set_font("Inter", style, size)` with "", "B", "I", "BI".
FONT_FILES = {
    "": "Inter-Regular.ttf",
    "B": "Inter-Bold.ttf",
    "I": "Inter-Italic.ttf",
    "BI": "Inter-BoldItalic.ttf",
}


class FontsMissingError(FileNotFoundError):
    """Required bundled font files are not present."""

    def __init__(self, missing: list[Path], font_dir: Path):
        self.missing = missing
        self.font_dir = font_dir
        names = ", ".join(p.name for p in missing)
        super().__init__(f"Missing font files in {font_dir}: {names}")


def register_fonts(pdf: FPDF, font_dir: str | Path = FONT_DIR) -> FPDF:
    """add_font every required Inter style; raise FontsMissingError listing absent files."""
    font_dir = Path(font_dir)
    missing = [font_dir / f for f in FONT_FILES.values() if not (font_dir / f).is_file()]
    if missing:
        raise FontsMissingError(missing, font_dir)
    for style, fname in FONT_FILES.items():
        pdf.add_font(FONT_FAMILY, style, str(font_dir / fname))
    return pdf


def new_document(cfg: Config, font_dir: str | Path = FONT_DIR) -> FPDF:
    """Create an empty FPDF in mm sized from `cfg.page_dimensions`, no auto page breaks."""
    pdf = FPDF(unit="mm", format=tuple(cfg.page_dimensions))
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.set_title(f"Agenda {cfg.year}")
    pdf.set_creator(f"agenda-gen {__version__}")
    pdf.set_author("agenda-gen")
    register_fonts(pdf, font_dir)
    return pdf


def add_page(pdf: FPDF, cfg: Config, page_number: int | None = None) -> Grid:
    """Add the next page and return its Grid (side from the 1-based page number).

    ``page_number`` is the page's real number in the agenda (default: next in this document);
    ``render_pages`` passes it so a partial document keeps correct margins and sides.

    fpdf2 l/r margins are set to the grid's safe-area margins for that page (top/bottom stay 0).
    """
    number = page_number or pdf.page + 1
    grid = Grid.for_page(cfg, number)
    pdf.add_page()
    pdf.set_left_margin(grid.left)
    pdf.set_right_margin(grid.right)
    if cfg.debug_grid:
        draw_debug_grid(pdf, grid, number)
    pdf.set_xy(grid.safe.x, grid.safe.y)
    return grid


def add_blank_pages(pdf: FPDF, n: int, cfg: Config) -> FPDF:
    for _ in range(n):
        add_page(pdf, cfg)
    return pdf


def write_pdf(pdf: FPDF, path: str | Path = DEFAULT_OUTPUT) -> Path:
    """Write the document, creating parent directories."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def export_blank(cfg: Config, pages: int = 1, path: str | Path = DEFAULT_OUTPUT) -> Path:
    return write_pdf(add_blank_pages(new_document(cfg), pages, cfg), path)


def _render_plan(
    cfg: Config,
    plan: PagePlan,
    indices: Iterable[int] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> FPDF:
    """Draw plan entries into a new document; ``indices`` (0-based, ascending) or all.

    One PDF page per entry (blank for ``page_class=None``); each page instance is drawn
    once, after its last page is added, with the grids of all its pages. Every page gets its
    real plan page number. A multi-page instance is always drawn whole.

    ``progress(done, total)`` is called after each page is added; it never changes the output.
    """
    chosen = range(len(plan)) if indices is None else indices
    todo = sorted({j for i in chosen for j in _instance_range(plan, i)})
    pdf = new_document(cfg)
    grids: list[Grid] = []
    for i in todo:
        entry = plan[i]
        grid = add_page(pdf, cfg, entry.page_number)
        if entry.page_in_instance == 0:
            grids = []
        grids.append(grid)
        last = entry.page_in_instance == (entry.page_class.pages - 1 if entry.page_class else 0)
        if entry.page_class is not None and last:
            entry.page_class().draw(pdf, entry.ctx, cfg, grids)
        if progress is not None:
            progress(pdf.page, len(todo))
    return pdf


def render_pages(cfg: Config, plan: PagePlan, indices: Iterable[int]) -> bytes:
    """PDF bytes with only the plan entries at ``indices`` (0-based), in plan order.

    Duplicates are ignored; no index raises ValueError; an out-of-range index raises IndexError. Pages keep their real
    page number (margins, left/right side). Rendering every index gives the same document
    as ``export_agenda``.
    """
    wanted = sorted(set(indices))
    if not wanted:
        raise ValueError("render_pages needs at least one page index")
    for i in wanted:
        if not 0 <= i < len(plan):
            raise IndexError(f"page index {i} out of range (0..{len(plan) - 1})")
    pdf = _render_plan(cfg, plan, wanted)
    data = bytes(pdf.output())
    todo = sorted({j for i in wanted for j in _instance_range(plan, i)})
    if len(todo) == len(wanted):
        return data
    # A multi-page instance had to be drawn whole: drop the pages that were not requested.
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    for pos, j in enumerate(todo):
        if j in wanted:
            writer.add_page(reader.pages[pos])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _instance_range(plan: PagePlan, i: int) -> range:
    start = i - plan[i].page_in_instance
    size = plan[i].page_class.pages if plan[i].page_class else 1
    return range(start, start + size)


def export_agenda(
    cfg: Config,
    path: str | Path = DEFAULT_OUTPUT,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Render the full agenda by iterating ``build_plan(cfg)`` (see ``_render_plan``).

    Optional ``progress(done_pages, total_pages)`` is called while drawing (not while writing).
    """
    from agenda.assembler import build_plan

    return write_pdf(_render_plan(cfg, build_plan(cfg), progress=progress), path)
