import pytest
from pypdf import PdfReader

from agenda.__main__ import main
from agenda.config import Config
from agenda.exporter import export_blank, new_document

MM = 72 / 25.4


def _sizes(path):
    r = PdfReader(path)
    return [(float(p.mediabox.width) / MM, float(p.mediabox.height) / MM) for p in r.pages]


def test_default_size_and_page_count(tmp_path):
    cfg = Config()
    w, h = cfg.page_dimensions
    out = export_blank(cfg, 3, tmp_path / "sub" / "a.pdf")
    sizes = _sizes(out)
    assert len(sizes) == 3
    for sw, sh in sizes:
        assert sw == pytest.approx(w, abs=0.1)
        assert sh == pytest.approx(h, abs=0.1)


def test_landscape_custom(tmp_path):
    out = export_blank(Config(page_size="200x100", orientation="landscape"), 1, tmp_path / "b.pdf")
    (sw, sh), = _sizes(out)
    assert (round(sw), round(sh)) == (200, 100)


def test_no_auto_page_break_and_metadata():
    pdf = new_document(Config(year=2027))
    assert pdf.auto_page_break is False
    assert "2027" in pdf.title


def test_cli_writes_pdf(tmp_path):
    out = tmp_path / "c.pdf"
    assert main(["-o", str(out), "--pages", "2", "--page-size", "a5"]) == 0
    sizes = _sizes(out)
    assert len(sizes) == 2
    assert round(sizes[0][0]) == 148 and round(sizes[0][1]) == 210
