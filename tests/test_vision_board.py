import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import LANGUAGES, STRINGS
from agenda.pages.value_added import VisionBoard as VB

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_vision_board():
    assert get_page("vision_board") is VB
    assert VB in pages_by_category("value_added")
    assert (VB.category, VB.section, VB.pages) == ("value_added", "value_added", 1)


def test_single_instance():
    assert len(VB().instances(Config())) == 1


def test_layout_rule():
    for rows in range(80):
        lay = VB.layout(rows, 40)
        assert lay.cols == 3 and 1 <= lay.nrows <= VB.MAX_GRID_ROWS
        top = VB.INTRO_ROWS + VB.WORD_ROWS + VB.GAP_ROWS
        if rows >= top + VB.MIN_CELL_ROWS:
            used = top + lay.nrows * lay.cell_rows + (lay.nrows - 1) * VB.GAP_ROWS
            assert used <= rows and lay.cell_rows >= VB.MIN_CELL_ROWS
    assert VB.layout(60, 3 * VB.MIN_CELL_W - 1).cols == 2
    assert VB.layout(60, 3 * VB.MIN_CELL_W).cols == 3


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    g = Grid.from_config(Config(page_size=size))
    lay = VB.layout(g.rows, g.safe.w / g.baseline)
    top = VB.INTRO_ROWS + VB.WORD_ROWS + VB.GAP_ROWS
    assert lay.cell_rows > VB.CAPTION_ROWS
    assert top + lay.nrows * lay.cell_rows + (lay.nrows - 1) * VB.GAP_ROWS <= g.rows


@pytest.mark.parametrize("lang", LANGUAGES)
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(VB, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, title, sub in (
        ("es", "Tablero de visión", "Mi visión para 2027"),
        ("en", "Vision board", "My vision for 2027"),
    ):
        text = PdfReader(io.BytesIO(render_page(VB, Config(language=lang, year=2027)))).pages[0]
        text = text.extract_text()
        assert title in text and sub in text
        assert STRINGS[lang]["vision.word"] in text


def test_plan_has_vision_board_only_when_listed():
    plan = build_plan(Config(pages=["vision_board"]))
    assert [e.page_class for e in plan].count(VB) == 1
    assert VB not in [e.page_class for e in build_plan(Config())]
