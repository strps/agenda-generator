import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.value_added import Travel

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_travel():
    assert get_page("travel") is Travel
    assert Travel in pages_by_category("value_added")
    assert (Travel.category, Travel.section) == ("value_added", "value_added")
    assert Travel.pages == 1


def test_instance_count():
    assert len(Travel().instances(Config())) == 1
    assert len(Travel(count=3).instances(Config())) == 3
    assert Travel(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Travel(count=-1)


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_rows(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    lay = Travel.layout(rows)
    assert Travel.FIXED_ROWS + lay.day_rows + lay.pack_rows <= rows
    assert lay.day_rows >= 1 and lay.pack_rows >= 1


def test_layout_rule():
    # 30 rows: 23 free, 60% (13) itinerary, rest packing, two columns
    assert Travel.layout(30) == (13, 10, 2)
    assert Travel.layout(Travel.TWO_COL_ROWS - 1).pack_cols == 1
    assert Travel.layout(Travel.TWO_COL_ROWS).pack_cols == 2
    assert Travel.layout(100).day_rows == Travel.MAX_DAYS


def test_layout_tiny_never_negative():
    for rows in range(Travel.FIXED_ROWS + 1):
        assert Travel.layout(rows)[:2] == (0, 0)


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Travel, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("size", SIZES)
def test_one_checkbox_per_packing_row(size):
    cfg = Config(page_size=size)
    lay = Travel.layout(Grid.from_config(cfg).rows)
    data = render_page(Travel, cfg)
    n = 0

    def on_op(op, args, cm, tm):
        nonlocal n
        n += op == b"re"

    PdfReader(io.BytesIO(data)).pages[0].extract_text(visitor_operand_before=on_op)
    assert n == lay.pack_rows * lay.pack_cols


@pytest.mark.parametrize(
    ("lang", "words"),
    (
        (
            "es",
            (
                "Planificador de viaje",
                "Destino",
                "Desde",
                "Hasta",
                "Presupuesto",
                "Itinerario",
                "Día 1",
                "Equipaje",
            ),
        ),
        (
            "en",
            (
                "Travel planner",
                "Destination",
                "From",
                "To",
                "Budget",
                "Itinerary",
                "Day 1",
                "Packing list",
            ),
        ),
    ),
)
def test_localized_text(lang, words):
    text = PdfReader(io.BytesIO(render_page(Travel, Config(language=lang)))).pages[0]
    text = text.extract_text()
    for w in words:
        assert w in text


def test_plan_includes_travel_only_when_listed():
    plan = build_plan(Config(pages=["travel"]))
    assert [e.page_class for e in plan].count(Travel) == 1
    assert Travel not in [e.page_class for e in build_plan(Config())]
