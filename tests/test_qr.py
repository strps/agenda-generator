import io

import pytest
from helpers import assert_in_safe_area, render_page
from pydantic import ValidationError
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import QR_MAX_CHARS, QR_MAX_COUNT, Config
from agenda.grid import Grid
from agenda.pages.value_added import QRCodes

SIZES = ("a5", "b6", "letter")


def _urls(n):
    return [f"https://example.com/{i}" for i in range(n)]


def _per_page(cfg):
    g = Grid.from_config(cfg)
    return QRCodes.layout(g.content.w, g.content.h, g.baseline, g.gutter).per_page


def test_registered_as_value_added_qr():
    assert get_page("qr") is QRCodes
    assert QRCodes in pages_by_category("value_added")
    assert (QRCodes.category, QRCodes.section) == ("value_added", "value_added")
    assert QRCodes.pages == 1


@pytest.mark.parametrize("size", SIZES)
def test_instances_from_url_count(size):
    k = _per_page(Config(page_size=size))
    assert k >= 4
    for n, pages in ((0, 0), (1, 1), (k, 1), (k + 1, 2), (2 * k + 1, 3)):
        cfg = Config(page_size=size, qr_urls=_urls(n))
        ctxs = QRCodes().instances(cfg)
        assert len(ctxs) == pages
        assert [u for c in ctxs for u in c["urls"]] == cfg.qr_urls


@pytest.mark.parametrize("size", SIZES)
def test_layout_rule(size):
    g = Grid.from_config(Config(page_size=size))
    c = g.content
    lay = QRCodes.layout(c.w, c.h, g.baseline, g.gutter)
    assert lay.cols == 2 and lay.rows in (2, 3)
    assert lay.cols * lay.cell_w + g.gutter <= c.w + 1e-6
    assert lay.rows * lay.cell_h + (lay.rows - 1) * g.gutter <= c.h + 1e-6
    assert lay.side + QRCodes.CAPTION_ROWS * g.baseline <= lay.cell_h + 1e-6
    assert lay.side <= lay.cell_w + 1e-6


def test_layout_rule_synthetic():
    assert QRCodes.layout(100, 300, 5, 5).rows == 3
    assert QRCodes.layout(100, 120, 5, 5).rows == 2


def test_matrix_square_and_has_finder_pattern():
    m = QRCodes.matrix("https://example.com")
    assert len(m) == len(m[0]) >= 21
    assert all(m[0][:7]) and all(m[6][:7])


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    k = _per_page(Config(page_size=size))
    cfg = Config(language=lang, page_size=size, qr_urls=_urls(k) + ["https://x.org/" + "a" * 150])
    data = render_page(QRCodes, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 2
    assert_in_safe_area(data, cfg)


def test_rect_count_matches_dark_modules():
    urls = ["https://example.com/a", "https://example.com/b"]
    cfg = Config(qr_urls=urls)
    data = render_page(QRCodes, cfg)
    content = PdfReader(io.BytesIO(data)).pages[0].get_contents().get_data()
    dark = sum(sum(row) for u in urls for row in QRCodes.matrix(u))
    assert content.count(b" re") - dark == 0


@pytest.mark.parametrize(
    ("lang", "words"),
    (("es", ("Códigos QR", "Nombre")), ("en", ("QR codes", "Name"))),
)
def test_localized_text(lang, words):
    cfg = Config(language=lang, qr_urls=["https://example.com"])
    text = PdfReader(io.BytesIO(render_page(QRCodes, cfg))).pages[0].extract_text()
    for w in words:
        assert w in text
    assert "https://example.com" in text


def test_config_validation():
    assert Config().qr_urls == []
    assert Config(qr_urls=["  https://a.org  ", "plain text"]).qr_urls == [
        "https://a.org",
        "plain text",
    ]
    for bad in ([""], ["   "], ["x" * (QR_MAX_CHARS + 1)], ["u"] * (QR_MAX_COUNT + 1)):
        with pytest.raises(ValidationError):
            Config(qr_urls=bad)
    assert len(Config(qr_urls=["x" * QR_MAX_CHARS] * QR_MAX_COUNT).qr_urls) == QR_MAX_COUNT


def test_plan_includes_qr_only_when_listed():
    def count(cfg):
        return [e.page_class for e in build_plan(cfg)].count(QRCodes)

    k = _per_page(Config())
    assert count(Config(pages=["qr"], qr_urls=_urls(k + 1))) == 2
    assert count(Config(pages=["qr"])) == 0  # listed with no URLs: plan still builds
    assert count(Config(qr_urls=_urls(3))) == 0
