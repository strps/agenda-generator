import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.calendar import month_grid
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.i18n import Strings
from agenda.pages.core import Monthly


def test_registered_as_core_monthly():
    assert get_page("monthly") is Monthly
    assert Monthly in pages_by_category("core")
    assert (Monthly.category, Monthly.section, Monthly.pages) == ("core", "monthly", 1)


def test_twelve_instances():
    assert [c["month"] for c in Monthly().instances(Config())] == list(range(1, 13))


@pytest.mark.parametrize("week_start", ["monday", "sunday"])
@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4", "letter"])
def test_renders_valid_pdf_in_safe_area(size, lang, week_start):
    cfg = Config(language=lang, page_size=size, week_start=week_start)
    data = render_page(Monthly, cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 12
    s = Strings(lang)
    for m, page in enumerate(reader.pages, 1):
        text = " ".join(page.extract_text().split())
        assert s("month.title", month=s.month_name(m), year=cfg.year) in text
        assert s("priorities") in text
    assert_in_safe_area(data, cfg)


def test_six_week_month_present_and_rendered():
    # August 2026 starts on Saturday: 6 rows with Monday start.
    cfg = Config(year=2026, week_start="monday")
    assert len(month_grid(2026, 8, "monday")) == 6
    data = render_page(Monthly, cfg)
    text = PdfReader(io.BytesIO(data)).pages[7].extract_text()
    assert "31" in text
    assert_in_safe_area(data, cfg)
