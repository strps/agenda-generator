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
    ((sw, sh),) = _sizes(out)
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


def test_fonts_registered_and_accents_render(tmp_path):
    from agenda.exporter import FONT_FAMILY, FONT_FILES, write_pdf

    pdf = new_document(Config())
    pdf.add_page()
    for style in FONT_FILES:
        pdf.set_font(FONT_FAMILY, style, 12)
        pdf.cell(0, 6, "Miércoles, año — ¿Qué tal? ñ Á É Í Ó Ú ü", new_x="LMARGIN", new_y="NEXT")
    out = write_pdf(pdf, tmp_path / "f.pdf")
    reader = PdfReader(out)
    assert "Miércoles, año" in reader.pages[0].extract_text()
    assert any("Inter" in str(f) for f in reader.pages[0]["/Resources"]["/Font"].values())


def test_missing_fonts_raise(tmp_path):
    from agenda.exporter import FONT_FILES, FontsMissingError

    with pytest.raises(FontsMissingError) as ei:
        new_document(Config(), font_dir=tmp_path)
    assert str(tmp_path) in str(ei.value)
    assert len(ei.value.missing) == len(FONT_FILES)
    assert "Inter-Regular.ttf" in str(ei.value)


def test_cli_exits_nonzero_when_fonts_missing(tmp_path, monkeypatch, capsys):
    import agenda.exporter as ex

    monkeypatch.setattr(ex, "FONT_DIR", tmp_path)
    monkeypatch.setattr(ex.new_document, "__defaults__", (tmp_path,))
    assert main(["-o", str(tmp_path / "x.pdf")]) == 1
    assert "Missing font files" in capsys.readouterr().err


def test_add_page_sets_per_page_grid_and_margins():
    from agenda.config import Config
    from agenda.exporter import add_page, new_document

    cfg = Config(inner_margin=15, outer_margin=10)
    pdf = new_document(cfg)
    for n in range(1, 5):
        grid = add_page(pdf, cfg)
        assert grid.side == ("right" if n % 2 else "left")
        assert pdf.l_margin == grid.left
        assert pdf.r_margin == grid.right
        assert pdf.get_x() == grid.safe.x
