import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.value_added import ExtrasGuide

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_physical_extras():
    assert get_page("physical_extras") is ExtrasGuide
    assert ExtrasGuide in pages_by_category("value_added")
    assert (ExtrasGuide.category, ExtrasGuide.section) == ("value_added", "value_added")
    assert ExtrasGuide.pages == 1


def test_one_instance():
    assert len(ExtrasGuide().instances(Config())) == 1


def test_layout_rule():
    n = len(ExtrasGuide.TIPS)
    r = ExtrasGuide.TIP_ROWS
    assert ExtrasGuide.layout(0) == (0, 0)
    assert ExtrasGuide.layout(2 * r) == (2, 0)
    assert ExtrasGuide.layout(100).tips == n
    assert ExtrasGuide.layout(n * r + 1).supply_rows == 0
    assert ExtrasGuide.layout(n * r + 2).supply_rows == 1
    assert ExtrasGuide.layout(1000).supply_rows == ExtrasGuide.SUPPLY_MAX_ROWS
    for rows in range(60):
        lay = ExtrasGuide.layout(rows)
        used = lay.tips * r + (lay.supply_rows + 1 if lay.supply_rows else 0)
        assert used <= rows


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_grid(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    lay = ExtrasGuide.layout(rows)
    assert lay.tips >= 1
    assert lay.tips * ExtrasGuide.TIP_ROWS <= rows


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(ExtrasGuide, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("lang", ("es", "en"))
def test_strings_present(lang):
    s = Strings(lang)
    for key in ("extras.title", "extras.supplies", *(f"extras.{k}" for k in ExtrasGuide.TIPS)):
        assert s(key).strip() and s(key) != key


@pytest.mark.parametrize(("lang", "title"), (("es", "Extras físicos"), ("en", "Physical extras")))
def test_localized_title(lang, title):
    text = (
        PdfReader(io.BytesIO(render_page(ExtrasGuide, Config(language=lang))))
        .pages[0]
        .extract_text()
    )
    assert title in text


def test_plan_includes_extras_only_when_listed():
    plan = build_plan(Config(pages=["physical_extras"]))
    assert [e.page_class for e in plan].count(ExtrasGuide) == 1
    assert ExtrasGuide not in [e.page_class for e in build_plan(Config())]
