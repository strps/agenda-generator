"""Per-font text color and size scale (font_*_color, font_*_size) via draw.set_font/AgendaPDF."""

import io

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from agenda import templates as T
from agenda.catalog import catalog_rows
from agenda.config import Config
from agenda.draw import color, set_font
from agenda.exporter import add_page, export_agenda, new_document
from agenda.pdfdoc import AgendaPDF, _rgb255


def _doc(**kw):
    cfg = Config(**kw)
    pdf = new_document(cfg)
    add_page(pdf, cfg)
    return pdf


def test_defaults_are_neutral():
    pdf = _doc()
    assert isinstance(pdf, AgendaPDF)
    assert pdf.agenda_font_scale == {"primary": 1.0, "secondary": 1.0}
    assert pdf.agenda_font_colors == {}
    set_font(pdf, "primary", "B", 12)
    assert pdf.font_size_pt == 12


def test_config_fields_and_yaml_keys():
    c = Config(font_primary_color="1e6fd9", font_secondary_size=120)
    assert c.font_primary_color == "#1e6fd9" and c.font_secondary_color is None
    assert (c.font_primary_size, c.font_secondary_size) == (100, 120)
    for bad in (
        {"font_primary_size": 49},
        {"font_secondary_size": 201},
        {"font_primary_color": "x"},
    ):
        with pytest.raises(ValidationError):
            Config(**bad)
    style = T.section(T.STYLING).fields
    assert style["primary_color"] == "font_primary_color"
    assert style["secondary_size"] == "font_secondary_size"


def test_size_scale_per_role():
    pdf = _doc(font_primary_size=150, font_secondary_size=80)
    set_font(pdf, "primary", "B", 10)
    assert pdf.font_size_pt == pytest.approx(15)
    set_font(pdf, "secondary", "", 10)
    assert pdf.font_size_pt == pytest.approx(8)


def test_font_color_replaces_plain_text_only():
    pdf = _doc(font_primary_color="#ff0000", font_secondary_color="#0000ff")
    ink, accent, muted = color(pdf, "ink"), color(pdf, "accent"), color(pdf, "muted")
    pdf.set_text_color(*ink)
    set_font(pdf, "primary", "B", 10)
    assert _rgb255(pdf.text_color) == (255, 0, 0)
    set_font(pdf, "secondary", "", 10)  # role change re-applies
    assert _rgb255(pdf.text_color) == (0, 0, 255)
    pdf.set_text_color(*accent)  # semantic colors are kept
    assert _rgb255(pdf.text_color) == accent
    pdf.set_text_color(*muted)
    set_font(pdf, "primary", "B", 10)
    assert _rgb255(pdf.text_color) == muted
    pdf.set_text_color(0, 0, 0)  # black (the PDF default) counts as plain text too
    assert _rgb255(pdf.text_color) == (255, 0, 0)


def test_role_without_color_keeps_asked_color():
    pdf = _doc(font_secondary_color="#00ff00")
    ink = color(pdf, "ink")
    pdf.set_text_color(*ink)
    set_font(pdf, "secondary", "", 9)
    assert _rgb255(pdf.text_color) == (0, 255, 0)
    set_font(pdf, "primary", "B", 9)
    assert _rgb255(pdf.text_color) == ink


def test_never_set_text_color_uses_font_color():
    pdf = _doc(font_primary_color="#123456")
    set_font(pdf, "primary", "B", 9)
    assert _rgb255(pdf.text_color) == (0x12, 0x34, 0x56)


def _text(pdf) -> str:
    return PdfReader(io.BytesIO(bytes(pdf.output()))).pages[0].extract_text()


def test_cell_shortens_overflowing_text_only_when_scaled_up():
    long = "Independence Day of a very long holiday name"
    for size, shortened in ((100, False), (200, True)):
        pdf = _doc(font_secondary_size=size)
        set_font(pdf, "secondary", "", 9)
        pdf.set_xy(10, 10)
        pdf.cell(30, 5, long)
        pdf.set_xy(10, 20)
        pdf.cell(0, 5, "zero width is never shortened")
        text = _text(pdf)
        assert ("…" in text) == shortened, size
        assert "zero width is never shortened" in text


@pytest.mark.parametrize("size", [50, 200])
def test_full_export_at_extreme_sizes(tmp_path, size):
    pages = [str(r["id"]) for r in catalog_rows()]
    cfg = Config(
        year=2027,
        pages=pages,
        qr_urls=["https://example.com"],
        daily_quotes=True,
        font_primary_size=size,
        font_secondary_size=size,
        font_primary_color="#1e6fd9",
        font_secondary_color="#2a2a2a",
    )
    out = export_agenda(cfg, tmp_path / "a.pdf")
    assert len(PdfReader(out).pages) > 300
