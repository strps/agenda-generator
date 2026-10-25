import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.value_added import Media

SIZES = ("a5", "b6", "letter")


def _layout(size):
    g = Grid.from_config(Config(page_size=size))
    type_w = 8.0  # stand-in for the measured label width
    lay = Media.layout(
        g.rows, g.safe.w, type_w, g.span_width(Media.DATE_COLS), g.span_width(Media.TITLE_COLS), g
    )
    return g, type_w, lay


def test_registered_as_value_added_media_log():
    assert get_page("media_log") is Media
    assert Media in pages_by_category("value_added")
    assert (Media.category, Media.section) == ("value_added", "value_added")
    assert Media.pages == 1


def test_instance_count():
    assert len(Media().instances(Config())) == 1
    assert len(Media(count=3).instances(Config())) == 3
    assert Media(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Media(count=-1)


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_width_and_rows(size):
    g, type_w, lay = _layout(size)
    gaps = g.gutter * (3 if lay.show_date else 2)
    date = g.span_width(Media.DATE_COLS) if lay.show_date else 0
    total = type_w + g.span_width(Media.TITLE_COLS) + date + gaps + Media.rating_width(lay.circle_d)
    assert total <= g.safe.w
    assert 1 + lay.rows * Media.ROW_ROWS <= g.rows
    assert lay.rows >= 1


def test_layout_rule_shrinks_circles_before_dropping_date():
    g, type_w, _ = _layout("a5")
    date_w, title = g.span_width(Media.DATE_COLS), g.span_width(Media.TITLE_COLS)
    big = Media.layout(40, 1000.0, type_w, date_w, title, g)
    assert (big.circle_d, big.show_date) == (g.baseline * Media.CIRCLE_RATIOS[0], True)
    need = lambda r: type_w + title + date_w + 3 * g.gutter + Media.rating_width(g.baseline * r)
    mid = Media.layout(40, need(Media.CIRCLE_RATIOS[1]), type_w, date_w, title, g)
    assert (mid.circle_d, mid.show_date) == (g.baseline * Media.CIRCLE_RATIOS[1], True)
    tight = Media.layout(40, need(Media.CIRCLE_RATIOS[-1]) - 0.1, type_w, date_w, title, g)
    assert tight.show_date is False and tight.circle_d >= g.baseline * Media.CIRCLE_RATIOS[-1]


def test_layout_rows_never_negative():
    g, type_w, _ = _layout("b6")
    assert Media.layout(0, 100.0, type_w, 10.0, 20.0, g).rows == 0
    assert Media.layout(1, 100.0, type_w, 10.0, 20.0, g).rows == 0


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Media, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("size", SIZES)
def test_five_circles_per_row(size):
    cfg = Config(page_size=size)
    g, _, _ = _layout(size)
    data = render_page(Media, cfg)
    content = PdfReader(io.BytesIO(data)).pages[0].get_contents().get_data().decode("latin-1")
    # fpdf draws each ellipse with 3 bezier curves ("c")
    curves = sum(1 for ln in content.splitlines() if ln.split() and ln.split()[-1] == "c")
    rows = Media.layout(
        g.rows, g.safe.w, 8.0, g.span_width(Media.DATE_COLS), g.span_width(Media.TITLE_COLS), g
    ).rows
    assert curves == rows * Media.RATING * 3


@pytest.mark.parametrize(
    ("lang", "words"),
    (
        ("es", ("Libros, películas y series", "Libro", "Película", "Serie", "Título", "Nota")),
        ("en", ("Books, movies and series", "Book", "Movie", "Series", "Title", "Rating")),
    ),
)
def test_localized_text(lang, words):
    text = PdfReader(io.BytesIO(render_page(Media, Config(language=lang)))).pages[0]
    text = text.extract_text()
    for w in words:
        assert w in text


def test_plan_includes_media_only_when_listed():
    plan = build_plan(Config(pages=["media_log"]))
    assert [e.page_class for e in plan].count(Media) == 1
    assert Media not in [e.page_class for e in build_plan(Config())]
