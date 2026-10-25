import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.value_added import Gratitude

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_gratitude():
    assert get_page("gratitude") is Gratitude
    assert Gratitude in pages_by_category("value_added")
    assert (Gratitude.category, Gratitude.section) == ("value_added", "value_added")
    assert Gratitude.pages == 1


def test_instance_count():
    assert len(Gratitude().instances(Config())) == 1
    assert len(Gratitude(count=3).instances(Config())) == 3
    assert Gratitude(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Gratitude(count=-1)


def test_layout_rule():
    # fixed rows = 1 date + 5 labels + 4 gaps = 10; the rest splits over 5 blocks
    assert Gratitude.layout(27) == (3, 5)  # 17 -> 3 each for 4 blocks, remainder to last
    assert Gratitude.layout(40) == (6, 6)
    assert Gratitude.layout(44) == (6, 10)
    assert Gratitude.layout(0) == (1, 1)


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    lines, last = Gratitude.layout(rows)
    assert lines >= 3
    assert 1 + 5 + 4 + lines * 4 + last <= rows


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Gratitude, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize(
    ("lang", "words"),
    (
        ("es", ("Diario de gratitud", "Fecha", "Estoy agradecido", "Mejor momento", "Intención")),
        ("en", ("Gratitude journal", "Date", "I am grateful", "Best moment", "Intention")),
    ),
)
def test_localized_text(lang, words):
    text = PdfReader(io.BytesIO(render_page(Gratitude, Config(language=lang)))).pages[0]
    text = text.extract_text()
    for w in words:
        assert w in text


def test_plan_includes_gratitude_only_when_listed():
    plan = build_plan(Config(pages=["gratitude"]))
    assert [e.page_class for e in plan].count(Gratitude) == 1
    assert Gratitude not in [e.page_class for e in build_plan(Config())]
