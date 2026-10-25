import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import month_name
from agenda.pages.optional import ImportantDates

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_important_dates():
    assert get_page("important_dates") is ImportantDates
    assert ImportantDates in pages_by_category("optional")
    cls = ImportantDates
    assert (cls.category, cls.section, cls.pages) == ("optional", "optional", 1)
    assert cls().instances(Config()) == [{}]


def test_layout_rule():
    assert ImportantDates.layout(48) == 6
    assert ImportantDates.layout(27) == 2
    assert ImportantDates.layout(12) == 1  # never below one row


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_rows(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    assert 6 * (ImportantDates.layout(rows) + 2) <= rows


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(ImportantDates, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize(
    ("lang", "title"), [("es", "Fechas importantes"), ("en", "Important dates")]
)
def test_localized_title_and_months(lang, title):
    text = PdfReader(io.BytesIO(render_page(ImportantDates, Config(language=lang)))).pages[0]
    text = text.extract_text()
    assert title in text
    for m in range(1, 13):
        assert month_name(m, lang) in text


def test_plan_includes_only_when_listed():
    plan = build_plan(Config(pages=["important_dates"]))
    assert [e.page_class for e in plan].count(ImportantDates) == 1
    assert ImportantDates not in [e.page_class for e in build_plan(Config())]
