import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.i18n import Strings
from agenda.pages.core import Yearly


def test_registered_as_core_front_back():
    assert get_page("yearly") is Yearly
    assert Yearly in pages_by_category("core")
    assert (Yearly.category, Yearly.section, Yearly.pages) == ("core", "front_back", 1)


def test_single_instance():
    assert Yearly().instances(Config()) == [{}]


@pytest.mark.parametrize("week_start", ["monday", "sunday"])
@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4"])
def test_renders_valid_pdf_in_safe_area(size, lang, week_start):
    cfg = Config(language=lang, page_size=size, week_start=week_start)
    data = render_page(Yearly, cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    s = Strings(lang)
    assert str(cfg.year) in text
    for m in range(1, 13):
        assert s.month_name(m) in text
    assert_in_safe_area(data, cfg)


def test_weekday_initials_follow_week_start():
    cfg = Config(language="en", week_start="sunday")
    text = PdfReader(io.BytesIO(render_page(Yearly, cfg))).pages[0].extract_text()
    assert "S M T W T F S" in " ".join(text.split())
