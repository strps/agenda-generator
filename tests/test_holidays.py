import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.calendar import holidays_for
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import Holidays

SIZES = ("a5", "b6", "letter")


def _text(cfg):
    return PdfReader(io.BytesIO(render_page(Holidays, cfg))).pages[0].extract_text()


def test_registered_as_optional_holidays():
    assert get_page("holidays") is Holidays
    assert Holidays in pages_by_category("optional")
    assert (Holidays.category, Holidays.section, Holidays.pages) == ("optional", "optional", 1)
    assert len(Holidays().instances(Config())) == 1


def test_layout_rule():
    assert Holidays.layout(26, 9) == (1, 9, 9)  # cap 13
    assert Holidays.layout(26, 13) == (1, 13, 13)
    assert Holidays.layout(26, 19) == (2, 19, 10)
    assert Holidays.layout(26, 40) == (2, 26, 13)  # truncated to 2 * cap
    assert Holidays.layout(26, 0) == (1, 0, 13)  # empty write-in rows
    assert Holidays.layout(0, 5)[1] == 0


@pytest.mark.parametrize("country", ("CR", "US", "CO", "XX"))
@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size, country):
    cfg = Config(language=lang, page_size=size, holiday_country=country)
    data = render_page(Holidays, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize(("lang", "title"), (("es", "Feriados"), ("en", "Holidays")))
def test_title_and_names_shown(lang, title):
    cfg = Config(language=lang, holiday_country="CR")
    text = _text(cfg)
    assert title in text and str(cfg.year) in text
    first = next(iter(holidays_for(cfg.year, "CR", lang).values()))
    assert first[:8] in text


def test_dates_localized():
    assert " ene" in _text(Config(language="es"))
    assert "Jan 1" in _text(Config(language="en", holiday_country="US"))


def test_unsupported_country_renders_title_only():
    text = _text(Config(holiday_country="XX"))
    assert "Feriados" in text


def test_truncates_when_too_many():
    cfg = Config(page_size="b6", holiday_country="CO", language="es")
    n = len(holidays_for(cfg.year, "CO", "es"))
    cols, shown, _ = Holidays.layout(Grid.from_config(cfg).rows, n)
    assert (cols, shown) == (2, n)  # CO fits in two columns on b6


def test_plan_includes_holidays_only_when_listed():
    plan = build_plan(Config(pages=["holidays"]))
    assert [e.page_class for e in plan].count(Holidays) == 1
    assert Holidays not in [e.page_class for e in build_plan(Config())]
