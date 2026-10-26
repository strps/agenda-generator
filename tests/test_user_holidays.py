import io
from datetime import date

import pytest
from pypdf import PdfReader

from agenda.calendar import holidays_for
from agenda.config import Config
from agenda.draw import HOLIDAY_STYLE, day_style_for, holiday_name_for, merged_holidays
from agenda.exporter import add_page, new_document
from agenda.pages.core import Daily, Weekly
from agenda.pages.optional import Holidays


@pytest.fixture
def cfg(tmp_path):
    f = tmp_path / "h.txt"
    f.write_text("03-15 My day\n01-01 Family\n", encoding="utf-8")
    return Config(year=2027, holiday_country="CR", language="es", holidays_file=f)


def text_of(page, cfg, pick=lambda c: True, pages=None) -> str:
    pdf = new_document(cfg)
    for ctx in page.instances(cfg):
        if pick(ctx):
            grids = [add_page(pdf, cfg) for _ in range(page.pages)]
            page.draw(pdf, ctx, cfg, grids)
    return " ".join(p.extract_text() for p in PdfReader(io.BytesIO(bytes(pdf.output()))).pages)


def test_names_and_style(cfg):
    assert holiday_name_for(cfg)(date(2027, 3, 15)) == "My day"
    assert day_style_for(cfg)(date(2027, 3, 15)) is HOLIDAY_STYLE
    lib = holidays_for(2027, "CR", "es")[date(2027, 1, 1)]
    assert holiday_name_for(cfg)(date(2027, 1, 1)) == f"{lib} · Family"


def test_shown_on_daily_weekly_holidays(cfg):
    d = date(2027, 3, 15)
    assert "My day" in text_of(Daily(), cfg, lambda c: c["date"] == d)
    assert "My day" in text_of(Weekly(), cfg)
    assert "My day" in text_of(Holidays(), cfg)


def test_no_file_equals_library():
    cfg = Config(year=2027, holiday_country="CR", language="es")
    assert merged_holidays(cfg) == holidays_for(2027, "CR", "es")


def test_unsupported_country_with_file(cfg):
    bad = cfg.model_copy(update={"holiday_country": "ZZ"})
    assert merged_holidays(bad) == {date(2027, 1, 1): "Family", date(2027, 3, 15): "My day"}
    with pytest.raises(ValueError):
        merged_holidays(bad.model_copy(update={"holidays_file": None}))
