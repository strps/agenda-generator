import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import weekday_names
from agenda.pages.value_added import Meals

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_meals():
    assert get_page("meals") is Meals
    assert Meals in pages_by_category("value_added")
    assert (Meals.category, Meals.section, Meals.pages) == ("value_added", "value_added", 1)
    assert len(Meals().instances(Config())) == 1


def test_layout_rule():
    assert Meals.layout(27) == (2, 10, 1)
    assert Meals.layout(34) == (2, 17, 2)
    assert Meals.layout(48) == (3, 24, 2)
    assert Meals.layout(0).grocery_rows == 0
    assert Meals.layout(500).day_rows == Meals.MAX_DAY_ROWS


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    day_rows, per_col, _ = Meals.layout(rows)
    assert per_col >= 5
    assert 1 + 7 * day_rows + 2 + per_col <= rows


@pytest.mark.parametrize("week_start", ("monday", "sunday"))
@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size, week_start):
    cfg = Config(language=lang, page_size=size, week_start=week_start)
    data = render_page(Meals, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("week_start", ("monday", "sunday"))
@pytest.mark.parametrize(
    ("lang", "words"),
    (
        ("es", ("Comidas y compras", "Desayuno", "Almuerzo", "Cena", "Lista de compras")),
        ("en", ("Meals and groceries", "Breakfast", "Lunch", "Dinner", "Grocery list")),
    ),
)
def test_localized_text_and_day_order(lang, words, week_start):
    cfg = Config(language=lang, week_start=week_start)
    text = PdfReader(io.BytesIO(render_page(Meals, cfg))).pages[0].extract_text()
    for w in words:
        assert w in text
    positions = [text.index(n) for n in weekday_names(lang, week_start, "short")]
    assert positions == sorted(positions)


@pytest.mark.parametrize("size", SIZES)
def test_one_checkbox_per_grocery_row(size):
    cfg = Config(page_size=size)
    layout = Meals.layout(Grid.from_config(cfg).rows)
    data = render_page(Meals, cfg)
    n = 0

    def on_op(op, args, cm, tm):
        nonlocal n
        n += op == b"re"

    PdfReader(io.BytesIO(data)).pages[0].extract_text(visitor_operand_before=on_op)
    planner = 7 * 3
    assert n == planner + layout.grocery_rows * layout.grocery_cols


def test_plan_includes_meals_only_when_listed():
    plan = build_plan(Config(pages=["meals"]))
    assert [e.page_class for e in plan].count(Meals) == 1
    assert Meals not in [e.page_class for e in build_plan(Config())]
