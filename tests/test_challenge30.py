import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.value_added import Challenge30

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_challenges30():
    assert get_page("challenges30") is Challenge30
    assert Challenge30 in pages_by_category("value_added")
    assert (Challenge30.category, Challenge30.section) == ("value_added", "value_added")
    assert Challenge30.pages == 1


def test_instance_count():
    assert len(Challenge30().instances(Config())) == 1
    assert len(Challenge30(count=3).instances(Config())) == 3
    assert Challenge30(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Challenge30(count=-1)


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_and_holds_30(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    lay = Challenge30.layout(rows)
    assert lay.cols * lay.grid_rows == Challenge30.DAYS
    used = Challenge30.FIXED_ROWS + lay.grid_rows * lay.cell_rows + lay.reflect_rows
    assert used == rows
    assert lay.reflect_rows >= Challenge30.MIN_REFLECT_ROWS


def test_layout_rule():
    assert Challenge30.layout(27) == (6, 5, 4, 2)  # b6: 6 cols, tall cells
    assert Challenge30.layout(34) == (5, 6, 4, 5)  # ties go to fewer columns
    assert Challenge30.layout(48) == (5, 6, 4, 19)  # capped cell height, rest is reflection
    # short pages shrink cells before dropping reflection rules
    assert Challenge30.layout(20).cell_rows < Challenge30.MAX_CELL_ROWS


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Challenge30, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("size", SIZES)
def test_exactly_30_day_cells(size):
    data = render_page(Challenge30, Config(page_size=size))
    n = 0

    def on_op(op, args, cm, tm):
        nonlocal n
        n += op == b"re"

    PdfReader(io.BytesIO(data)).pages[0].extract_text(visitor_operand_before=on_op)
    assert n == Challenge30.DAYS


@pytest.mark.parametrize(
    ("lang", "words"),
    (
        ("es", ("Reto de 30 días", "Mi reto", "Por qué", "Reflexión", "30")),
        ("en", ("30-day challenge", "My challenge", "Why", "Reflection", "30")),
    ),
)
def test_localized_text(lang, words):
    page = PdfReader(io.BytesIO(render_page(Challenge30, Config(language=lang)))).pages[0]
    text = page.extract_text()
    for w in words:
        assert w in text


def test_plan_includes_challenge_only_when_listed():
    plan = build_plan(Config(pages=["challenges30"]))
    assert [e.page_class for e in plan].count(Challenge30) == 1
    assert Challenge30 not in [e.page_class for e in build_plan(Config())]
