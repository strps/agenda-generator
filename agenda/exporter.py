"""PDF writing (fpdf2), bookmarks and internal links."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from agenda import __version__
from agenda.calendar import weeks_by_month
from agenda.config import Config
from agenda.draw import draw_debug_grid
from agenda.grid import Grid, side_for_page

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


def add_page(pdf: FPDF, cfg: Config) -> Grid:
    """Add the next page and return its Grid (side from the 1-based page number).

    fpdf2 l/r margins are set to the grid's safe-area margins for that page (top/bottom stay 0).
    """
    grid = Grid.for_page(cfg, pdf.page + 1)
    pdf.add_page()
    pdf.set_left_margin(grid.left)
    pdf.set_right_margin(grid.right)
    if cfg.debug_grid:
        draw_debug_grid(pdf, grid, pdf.page)
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


def export_agenda(cfg: Config, path: str | Path = DEFAULT_OUTPUT) -> Path:
    """TEMPORARY full-agenda render (Phase 3). Phase 4 (`build_plan`) replaces this.

    Order (plan section 7): cover, personal_info, yearly, then per month: monthly, then per owned
    week its weekly spread and that week's daily pages (dates inside ``cfg.year``); then notes,
    contacts, back_cover. A blank filler page is inserted when a page class with
    ``starts_on`` left/right would start on the other side. No booklet math, padding,
    ``daily_months`` or separate covers.
    """
    from agenda.pages.core import (
        BackCover,
        Contacts,
        Cover,
        Daily,
        Monthly,
        Notes,
        PersonalInfo,
        Weekly,
        Yearly,
    )

    pdf = new_document(cfg)

    def put(page, ctx) -> None:
        want = page.starts_on
        if want != "any" and side_for_page(pdf.page + 1) != want:
            add_page(pdf, cfg)  # blank filler
        grids = [add_page(pdf, cfg) for _ in range(page.pages)]
        page.draw(pdf, ctx, cfg, grids)

    for cls in (Cover, PersonalInfo, Yearly):
        put(cls(), {})
    monthly, weekly, daily = Monthly(), Weekly(), Daily()
    weekly_ctx = {(c["iso_year"], c["number"]): c for c in weekly.instances(cfg)}
    daily_ctx = {c["date"]: c for c in daily.instances(cfg)}
    for month, weeks in weeks_by_month(cfg.year, cfg.week_start).items():
        put(monthly, {"month": month})
        for week in weeks:
            if "weekly" in cfg.planners:
                put(weekly, weekly_ctx[(week.iso_year, week.number)])
            if "daily" in cfg.planners:
                for d in week.days:
                    if d in daily_ctx:
                        put(daily, daily_ctx[d])
    for cls in (Notes, Contacts, BackCover):
        put(cls(), {})
    return write_pdf(pdf, path)
