import pytest
from pypdf import PdfReader

from agenda.__main__ import main
from agenda.config import Config
from agenda.draw import draw_debug_grid
from agenda.exporter import add_page, export_blank, new_document
from agenda.grid import Grid


@pytest.mark.parametrize("size", ["half_letter", "a5"])
@pytest.mark.parametrize("side", ["left", "right"])
def test_overlay_does_not_raise(size, side):
    cfg = Config(page_size=size)
    pdf = new_document(cfg)
    pdf.add_page()
    draw_debug_grid(pdf, Grid.from_config(cfg, side), 1)


def test_cli_debug_grid_pages(tmp_path):
    out = tmp_path / "g.pdf"
    assert main(["--debug-grid", "--pages", "3", "-o", str(out)]) == 0
    assert len(PdfReader(str(out)).pages) == 3


def test_debug_grid_adds_content(tmp_path):
    plain = export_blank(Config(), 2, tmp_path / "a.pdf").stat().st_size
    dbg = export_blank(Config(debug_grid=True), 2, tmp_path / "b.pdf").stat().st_size
    assert dbg > plain


def test_add_page_with_overlay_returns_grid():
    cfg = Config(debug_grid=True)
    pdf = new_document(cfg)
    assert add_page(pdf, cfg).side == "right"
    assert add_page(pdf, cfg).side == "left"
